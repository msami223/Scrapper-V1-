# app.py

from flask import Flask, render_template, request, jsonify, send_file, Response
import os
from main_scraper import scrape_website_data, export_data_to_excel
import time
import threading
import json

app = Flask(__name__)

status_messages = []
total_urls = 0
urls_processed = 0
current_url = None
all_scraped_data = []
stop_current_url = False
scraping_thread = None
is_scraping = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    global total_urls, urls_processed, all_scraped_data, current_url, stop_current_url, scraping_thread, is_scraping
    
    # If already scraping, return a message
    if is_scraping:
        return jsonify({'message': 'Scraping already in progress.'})
    
    urls = request.json.get('urls', [])
    total_urls = len(urls)
    urls_processed = 0
    all_scraped_data = []
    status_messages.clear()  # Clear previous status messages
    stop_current_url = False
    is_scraping = True

    def run_scraping():
        global urls_processed, current_url, stop_current_url, is_scraping
        for url in urls:
            current_url = url
            stop_current_url = False
            status_messages.append(f"Starting scrape for {url}")
            
            try:
                scraped_data = scrape_website_data(url)
                
                # Check if we should skip this URL
                if stop_current_url:
                    status_messages.append(f"Skipped {url}")
                    urls_processed += 1
                    status_messages.append(f"Progress: {urls_processed}/{total_urls}")
                    continue
                    
                urls_processed += 1
                status_messages.append(f"Progress: {urls_processed}/{total_urls}")
                
                if scraped_data:
                    all_scraped_data.append(scraped_data)
                    status_messages.append(f"Successfully scraped data from {url}")
                else:
                    status_messages.append(f"Failed to scrape data from {url}")
            except Exception as e:
                status_messages.append(f"Error scraping {url}: {str(e)}")
                urls_processed += 1
                status_messages.append(f"Progress: {urls_processed}/{total_urls}")

        # Export final data
        if all_scraped_data:
            filename = "scraped_data.xlsx"
            export_data_to_excel(all_scraped_data, filename)
            status_messages.append(f"Data exported to {filename}")
        else:
            status_messages.append("No data scraped.")

        status_messages.append("Scraping process completed.")
        current_url = None
        is_scraping = False

    scraping_thread = threading.Thread(target=run_scraping)
    scraping_thread.start()

    return jsonify({'message': 'Scraping started.'})

@app.route('/skip_current', methods=['POST'])
def skip_current():
    global stop_current_url, current_url
    if current_url:
        stop_current_url = True
        return jsonify({'message': f'Skipping current URL: {current_url}'})
    else:
        return jsonify({'message': 'No URL is currently being processed.'})

@app.route('/download_current', methods=['POST'])
def download_current():
    global all_scraped_data
    if all_scraped_data:
        filename = "partial_data.xlsx"
        export_data_to_excel(all_scraped_data, filename)
        status_messages.append(f"Partial data exported to {filename}")
        return jsonify({'message': 'Partial data exported successfully.', 'filename': filename})
    else:
        return jsonify({'message': 'No data available to download yet.'})

@app.route('/status')
def status():
    def generate():
        while True:
            if status_messages:
                message = status_messages.pop(0)
                yield f"data: {message}\n\n"
            time.sleep(1)

    return Response(generate(), mimetype='text/event-stream')

@app.route('/download/<filename>')
def download(filename):
    file_path = os.path.join(os.getcwd(), filename)
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return jsonify({'error': 'File not found.'}), 404

if __name__ == '__main__':
    app.run(debug=True)