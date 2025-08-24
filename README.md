# FED Press Conference Scraper

**Download and extract text from Federal Reserve FOMC press conference transcripts with automated name tagging.**

A Python tool that scrapes PDF transcripts from federalreserve.gov, extracts clean text, and automatically tags key figures with `<NAME>` tags for data analysis and research.

## 🚀 Key Features

- **Automated PDF Download**: Batch download FOMC press conference transcripts
- **Text Extraction**: Clean text extraction using pdfplumber
- **Name Tagging**: Automatic identification and tagging names
- **Progress Tracking**: Visual progress bars for large datasets
- **Comprehensive Logging**: Detailed operation logs for debugging
- **Error Handling**: Robust retry logic and graceful failure handling

## 📋 Use Cases

- **ML Model Training**: Train and fine tune ML models
- **Financial Research**: Analyze FOMC meeting transcripts for policy insights
- **Data Science**: Extract structured text data for NLP analysis
- **Academic Research**: Study Federal Reserve communication patterns
- **Media Analysis**: Track mentions of key economic figures
- **Compliance**: Archive regulatory communications

## 🛠️ Quick Start

```bash
# Clone repository
git clone https://github.com/yourusername/fed-scraper.git
cd fed-scraper

# Setup virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run scraper
python main.py
```

## 📁 Input/Output

**Input**: Text file with dates (YYYYMMDD format)
```txt
20231213
20231101
20230920
```

**Output**: Clean text files with tagged names
```
<NAME>CHAIR POWELL</NAME>. Good afternoon. At the Federal Reserve, 
we are strongly committed to achieving the monetary policy goals 
that Congress has given us: maximum employment...
```

## ⚙️ Configuration

Customize behavior via `config.py`:

- Request timeouts and retry settings
- Output directories and file naming
- Rate limiting and delays
- Logging levels and file paths

## 🔧 Dependencies

- `requests` - HTTP client for PDF downloads
- `pdfplumber` - PDF text extraction
- `tqdm` - Progress bars for long operations

## 📊 Supported Data Sources

- **Federal Reserve Press Conferences**: FOMC meeting transcripts
- **Date Range**: 2020-present (configurable)
- **Format**: FOMC -> PDF → Clean text with name tags
- **Updates**: Real-time availability from federalreserve.gov

## 🎯 Target Audience

- Financial analysts and researchers
- Data scientists and NLP practitioners
- Academic researchers in economics
- Compliance and regulatory professionals
- Media and journalism professionals

## 📈 Performance

- **Speed**: Configurable rate limiting
- **Reliability**: Automatic retry with exponential backoff
- **Memory**: Efficient streaming PDF processing

## 🔒 Security & Ethics

- Respectful rate limiting to avoid server overload
- Transparent user agent identification
- Compliant with website terms of service

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make improvements
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Users must comply with federalreserve.gov terms of service and robots.txt guidelines.

---

**Keywords**: Federal Reserve, FOMC, press conference, transcript scraper, PDF extraction, name tagging, financial data, monetary policy, economic research, data science, Python

[Author](https://github.com/BigJonP)
