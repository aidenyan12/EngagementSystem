# 🌐 **RAG System URL Management Guide**

This guide explains how to add new URLs to the RAG (Retrieval-Augmented Generation) system for the ATL Chatbot.

## 📋 **Quick Reference**

| Method | Use Case | Command |
|--------|----------|---------|
| **Method 1** | Change base website | Edit `src/rag_system.py` line 37 |
| **Method 2** | Add specific URLs | `python src/manage_rag.py update-urls --urls "url1,url2"` |
| **Method 3** | Use config file | `python src/manage_rag.py update-config` |

---

## 🔧 **Method 1: Change Base URL**

### When to Use
- Switching to a completely different primary website
- Moving from one domain to another

### How to Do It
1. Open `src/rag_system.py`
2. Find line 37: `def __init__(self, base_url: str = "https://www.atlab.hku.hk/"):`
3. Change the URL: `def __init__(self, base_url: str = "https://your-new-site.com/"):`
4. Run update: `python src/manage_rag.py update`

### Example
```python
# Before
def __init__(self, base_url: str = "https://www.atlab.hku.hk/"):

# After  
def __init__(self, base_url: str = "https://www.arts.hku.hk/"):
```

---

## 🎯 **Method 2: Add Specific URLs**

### When to Use
- Adding specific pages or sections
- Including external relevant content
- One-time URL additions

### How to Do It
Use the command line with comma-separated URLs:

```bash
python src/manage_rag.py update-urls --urls "https://example.com/page1,https://example.com/page2,https://another-site.com/relevant-info"
```

### Example
```bash
# Add HKU Arts Faculty pages
python src/manage_rag.py update-urls --urls "https://www.arts.hku.hk/,https://www.arts.hku.hk/research/,https://www.arts.hku.hk/facilities/"
```

---

## ⚙️ **Method 3: Configuration File (Recommended)**

### When to Use
- Managing multiple URLs systematically
- Setting up complex scraping rules
- Team collaboration and version control
- Regular updates with same URL sets

### Configuration File: `data/rag_urls.json`

```json
{
  "base_url": "https://www.atlab.hku.hk/",
  "additional_urls": [
    "https://www.arts.hku.hk/",
    "https://www.arts.hku.hk/research/"
  ],
  "external_domains": [
    "www.arts.hku.hk"
  ],
  "url_patterns": {
    "include": [
      "**/atl/**",
      "**/arts-tech/**",
      "**/facilities/**"
    ],
    "exclude": [
      "**/admin/**",
      "**/private/**",
      "**/.pdf",
      "**/.zip"
    ]
  },
  "scraping_settings": {
    "max_pages": 50,
    "delay_seconds": 1,
    "timeout_seconds": 10,
    "respect_robots_txt": true
  }
}
```

### How to Use
```bash
# Use default config file (data/rag_urls.json)
python src/manage_rag.py update-config

# Use custom config file
python src/manage_rag.py update-config --config /path/to/custom-config.json
```

---

## 📊 **Configuration Options Explained**

### Basic Settings
- **`base_url`**: Primary website to scrape
- **`additional_urls`**: Specific URLs to include
- **`external_domains`**: Allowed external domains for link discovery

### Advanced Settings
- **`url_patterns.include`**: Only scrape URLs matching these patterns
- **`url_patterns.exclude`**: Skip URLs matching these patterns
- **`scraping_settings.max_pages`**: Maximum pages to scrape
- **`scraping_settings.delay_seconds`**: Delay between requests (be respectful!)

---

## 🚀 **Usage Examples**

### Example 1: Add University News
```json
{
  "base_url": "https://www.atlab.hku.hk/",
  "additional_urls": [
    "https://www.hku.hk/news/",
    "https://www.arts.hku.hk/news/"
  ]
}
```

### Example 2: Academic Resources
```json
{
  "additional_urls": [
    "https://www.hku.hk/research/",
    "https://www.arts.hku.hk/research/"
  ],
  "external_domains": [
    "www.hku.hk"
  ]
}
```

### Example 3: Multiple University Departments
```json
{
  "additional_urls": [
    "https://www.cs.hku.hk/",
    "https://www.eee.hku.hk/",
    "https://www.arch.hku.hk/"
  ],
  "external_domains": [
    "www.cs.hku.hk",
    "www.eee.hku.hk", 
    "www.arch.hku.hk"
  ]
}
```

---

## 🔍 **Checking What's Scraped**

### Check Status
```bash
python src/manage_rag.py status
```

### Test Retrieval
```bash
python src/manage_rag.py test
```

### View Scraped Data
The scraped data is stored in:
- **Raw data**: `data/rag_data/scraped_data.json`
- **Processed chunks**: `data/rag_data/chunks.json`
- **Metadata**: `data/rag_data/metadata.json`

---

## ⚠️ **Best Practices**

### 1. **Respect Robots.txt**
Always check the website's `robots.txt` file (e.g., `https://example.com/robots.txt`)

### 2. **Be Respectful with Delays**
Set appropriate delays between requests:
```json
"scraping_settings": {
  "delay_seconds": 2,
  "timeout_seconds": 15
}
```

### 3. **Filter Relevant Content**
Use URL patterns to avoid scraping unnecessary pages:
```json
"url_patterns": {
  "exclude": [
    "**/admin/**",
    "**/login/**",
    "**/.pdf",
    "**/images/**"
  ]
}
```

### 4. **Monitor Performance**
- Start with fewer URLs and increase gradually
- Check the quality of scraped content
- Monitor storage usage

---

## 🐛 **Troubleshooting**

### Common Issues

1. **"No pages scraped"**
   - Check internet connection
   - Verify URLs are accessible
   - Check for anti-bot protection

2. **"Permission denied"**
   - Some websites block automated requests
   - Check robots.txt
   - Consider using delays

3. **"Too much data"**
   - Reduce `max_pages`
   - Use URL patterns to filter content
   - Increase chunk size

### Getting Help
```bash
# Check current status
python src/manage_rag.py status

# Test retrieval
python src/manage_rag.py test

# View help
python src/manage_rag.py --help
```

---

## 🔄 **Regular Maintenance**

### Weekly Updates
```bash
# Update with current configuration
python src/manage_rag.py update-config
```

### Monthly Review
1. Check `data/rag_data/metadata.json` for statistics
2. Review and update `data/rag_urls.json`
3. Test retrieval quality with sample queries

### Automation
Consider setting up a cron job or scheduled task:
```bash
# Example cron job (runs daily at 2 AM)
0 2 * * * cd /path/to/atl-chatbot && python src/manage_rag.py update-config
```

---

## 📞 **Integration with Chatbot**

The updated RAG data is automatically used by the chatbot. After updating URLs:

1. **Restart the chatbot** if it's running
2. **Test with relevant queries** to verify new content is accessible
3. **Monitor response quality** and adjust URLs as needed

---

*This guide provides multiple flexible options for managing URLs in the RAG system. Choose the method that best fits your workflow and requirements!* 