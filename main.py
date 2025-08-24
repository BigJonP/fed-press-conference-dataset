"""
FED Press Conference PDF Scraper

This script downloads PDFs from FED Press Conferences hosted on federalreserve.gov
and extracts the raw text, saving it as .txt files.

The PDFs follow the format: FOMCpresconf<date>.pdf where date is YYYYMMDD
"""

import logging
import re
import time
from pathlib import Path
from typing import List, Optional, Tuple
from dataclasses import dataclass
import requests
import pdfplumber
from io import BytesIO
from tqdm import tqdm


from config import ScraperConfig


class ScraperError(Exception):
    """Custom exception for scraper-related errors"""

    pass


class FEDPressConferenceScraper:
    """Scraper for FED Press Conference PDFs"""

    def __init__(self, config: Optional[ScraperConfig] = None):
        """
        Initialize the scraper

        Args:
            config: Configuration object for the scraper
        """
        self.config = config or ScraperConfig()
        self.output_dir = Path(self.config.output_dir)
        self.output_dir.mkdir(exist_ok=True)

        self._setup_logging()

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "FED-Press-Conference-Scraper/1.0 (+https://github.com/<yourusername>/fed-scraper)"
            }
        )

        self._compile_regex_patterns()

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler("scraper.log"), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def _compile_regex_patterns(self) -> None:
        """Compile regex patterns for efficiency"""
        self.page_number_pattern = re.compile(r"Page \d+ of \d+")
        self.header_pattern = re.compile(
            r"[A-Za-z]+\s+\d{1,2}\s*,\s*\d{3}\s*\d\s+Chair\s+Powell\s*['\u2019\s]*s\s+Press\s+Conference\s+FINAL"
        )
        self.transcript_with_date_pattern = re.compile(
            r"Transcript\s+of\s+Chair\s+Powell\s*['\u2019\s]*s\s+Press\s+Conference\s+[A-Za-z]+\s+\d{1,2}\s*,\s*\d{3}\s*\d"
        )
        self.transcript_pattern = re.compile(
            r"Transcript\s+of\s+Chair\s+Powell\s*['\u2019\s]*s\s+Press\s+Conference"
        )
        self.whitespace_pattern = re.compile(r"\s+")

        self.names = self._load_names_from_file()

    def _load_names_from_file(self, filename: str = "names.txt") -> List[str]:
        """
        Load names from a text file for tagging

        Args:
            filename: Name of the file containing names

        Returns:
            List of names to tag
        """
        try:
            filepath = Path(filename)
            if not filepath.exists():
                self.logger.warning(f"Names file {filename} not found, no names will be tagged")
                return []

            with open(filepath, "r", encoding="utf-8") as f:
                names = [line.strip() for line in f if line.strip()]

            self.logger.info(f"Loaded {len(names)} names for tagging from {filename}")
            return names

        except Exception as e:
            self.logger.error(f"Error reading names file: {e}")
            return []

    def load_dates_from_file(self, filename: str = "press_conference_dates.txt") -> List[str]:
        """
        Load predefined dates from a text file

        Args:
            filename: Name of the file containing dates

        Returns:
            List of valid dates in YYYYMMDD format

        Raises:
            ScraperError: If there's an error reading the file
        """
        try:
            filepath = Path(filename)
            if not filepath.exists():
                raise FileNotFoundError(f"Date file {filename} not found")

            with open(filepath, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]

        except Exception as e:
            raise ScraperError(f"Error reading date file: {e}") from e

    def download_pdf(self, date_str: str) -> Optional[bytes]:
        """
        Download a PDF for a specific date with retry logic

        Args:
            date_str: Date in YYYYMMDD format

        Returns:
            PDF content if successful, None otherwise
        """
        filename = f"FOMCpresconf{date_str}.pdf"
        url = f"{self.config.base_url}{filename}"

        for attempt in range(self.config.max_retries):
            try:
                self.logger.info(f"Attempting to download: {url} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=self.config.request_timeout)

                if response.status_code == 200:
                    self.logger.info(f"Successfully downloaded: {filename}")
                    return response.content
                elif response.status_code == 404:
                    self.logger.warning(f"PDF not found for date {date_str}: {filename}")
                    return None
                else:
                    self.logger.warning(
                        f"Failed to download {filename}: HTTP {response.status_code}"
                    )

            except requests.exceptions.RequestException as e:
                self.logger.error(f"Error downloading {filename} (attempt {attempt + 1}): {e}")
                if attempt < self.config.max_retries - 1:
                    time.sleep(self.config.retry_delay)
                    continue
                else:
                    self.logger.error(
                        f"Failed to download {filename} after {self.config.max_retries} attempts"
                    )
                    return None

        return None

    def clean_extracted_text(self, text_content: str) -> str:
        """
        Clean extracted text by removing redundant data and formatting

        Args:
            text_content: Raw extracted text from PDF

        Returns:
            Cleaned text content
        """
        if not text_content:
            return text_content

        text_content = self.page_number_pattern.sub("", text_content)
        text_content = self.header_pattern.sub("", text_content)
        text_content = self.transcript_with_date_pattern.sub("", text_content)
        text_content = self.transcript_pattern.sub("", text_content)
        text_content = self.whitespace_pattern.sub(" ", text_content)

        text_content = self._tag_names_in_text(text_content)

        return text_content.strip()

    def _tag_names_in_text(self, text_content: str) -> str:
        """
        Tag names in text with <NAME> tags

        Args:
            text_content: Text content to process

        Returns:
            Text with names tagged
        """
        if not self.names:
            return text_content

        tagged_text = text_content

        for name in self.names:
            if name in tagged_text:
                pattern = r"\b" + re.escape(name) + r"\b"
                tagged_text = re.sub(pattern, f"<NAME>{name}</NAME>", tagged_text)

        return tagged_text

    def extract_text_from_pdf(self, pdf_content: bytes) -> str:
        """
        Extract text from PDF content

        Args:
            pdf_content: PDF file content

        Returns:
            Extracted text

        Raises:
            ScraperError: If there's an error extracting text
        """
        try:
            pdf_file = BytesIO(pdf_content)
            text_parts = []

            with pdfplumber.open(pdf_file) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                        else:
                            self.logger.warning(f"No text extracted from page {page_num}")
                    except Exception as e:
                        self.logger.warning(f"Error extracting text from page {page_num}: {e}")
                        continue

            if not text_parts:
                raise ScraperError("No text could be extracted from any page")

            return "\n".join(text_parts).strip()

        except Exception as e:
            raise ScraperError(f"Error extracting text from PDF: {e}") from e

    def save_text_file(self, date_str: str, text_content: str) -> bool:
        """
        Save extracted text to a file

        Args:
            date_str: Date in YYYYMMDD format
            text_content: Text content to save

        Returns:
            True if successful, False otherwise
        """
        if not text_content.strip():
            self.logger.warning(f"No text content to save for date {date_str}")
            return False

        filename = f"FOMCpresconf{date_str}.txt"
        filepath = self.output_dir / filename

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(text_content)

            self.logger.info(f"Saved text file: {filepath}")
            return True

        except Exception as e:
            self.logger.error(f"Error saving text file {filepath}: {e}")
            return False

    def clean_all_text_files(self) -> int:
        """
        Clean all existing text files in the output directory

        Returns:
            Number of successfully cleaned files
        """
        self.logger.info("Starting to clean all text files...")
        text_files = list(self.output_dir.glob("FOMCpresconf*.txt"))

        if not text_files:
            self.logger.info("No text files found to clean")
            return 0

        cleaned_count = 0
        failed_files = []

        for text_file in tqdm(text_files, desc="Cleaning text files"):
            try:
                with open(text_file, "r", encoding="utf-8") as f:
                    raw_content = f.read()

                cleaned_content = self.clean_extracted_text(raw_content)

                with open(text_file, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)

                cleaned_count += 1

            except Exception as e:
                self.logger.error(f"Error cleaning {text_file}: {e}")
                failed_files.append(str(text_file))
                continue

        if failed_files:
            self.logger.warning(f"Failed to clean {len(failed_files)} files: {failed_files}")

        self.logger.info(
            f"Cleaning completed. {cleaned_count}/{len(text_files)} files cleaned successfully"
        )
        return cleaned_count

    def process_date(self, date_str: str) -> bool:
        """
        Process a single date: download PDF, extract text, and save

        Args:
            date_str: Date in YYYYMMDD format

        Returns:
            True if successful, False otherwise
        """
        text_file = self.output_dir / f"FOMCpresconf{date_str}.txt"
        if text_file.exists():
            self.logger.info(f"Text file already exists for {date_str}, skipping")
            return True

        try:
            pdf_content = self.download_pdf(date_str)
            if pdf_content is None:
                return False

            text_content = self.extract_text_from_pdf(pdf_content)
            if not text_content:
                self.logger.warning(f"No text extracted from PDF for {date_str}")
                return False

            return self.save_text_file(date_str, text_content)

        except Exception as e:
            self.logger.error(f"Error processing date {date_str}: {e}")
            return False

    def scrape_predefined_dates(self) -> Tuple[int, int]:
        """
        Scrape press conferences using predefined dates from file

        Returns:
            Tuple of (success_count, total_count)
        """
        try:
            dates = self.load_dates_from_file()
            if not dates:
                self.logger.warning("No dates loaded from file")
                return 0, 0

            self.logger.info(f"Scraping {len(dates)} predefined dates")

            success_count = 0
            total_count = len(dates)

            for date_str in tqdm(dates, desc="Scraping press conferences"):
                if self.process_date(date_str):
                    success_count += 1

                time.sleep(self.config.delay)

            self.logger.info(
                f"Scraping completed. Total: {total_count}, Successful: {success_count}"
            )
            return success_count, total_count

        except Exception as e:
            self.logger.error(f"Error during scraping: {e}")
            raise ScraperError(f"Scraping failed: {e}") from e


def main() -> None:
    """Main function to run the scraper"""
    try:
        scraper = FEDPressConferenceScraper()

        scraper.logger.info("Starting FED Press Conference scraper...")
        scraper.logger.info(
            "This will download PDFs and extract text from predefined FOMC press conference dates."
        )
        scraper.logger.info("The process may take some time depending on the number of files.")

        success, total = scraper.scrape_predefined_dates()
        scraper.logger.info(f"Scraping completed! {success}/{total} files processed successfully.")

        scraper.logger.info("Starting text cleaning process...")
        cleaned_count = scraper.clean_all_text_files()
        scraper.logger.info(f"Text cleaning completed! {cleaned_count} files cleaned successfully.")

    except KeyboardInterrupt:
        scraper.logger.info("Scraping interrupted by user")
    except Exception as e:
        scraper.logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
