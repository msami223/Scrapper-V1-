import requests
from bs4 import BeautifulSoup
import re
import pandas as pd


def fetch_and_parse_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def find_favicon(soup, base_url):
    favicon = None
    link_tag = soup.find('link', rel='icon')
    if not link_tag:
        link_tag = soup.find('link', rel='shortcut icon')
    if link_tag and 'href' in link_tag.attrs:
        favicon = requests.compat.urljoin(base_url, link_tag['href'])
    return favicon


def find_social_media_links(soup):
    social_media = {
        'Facebook': None,
        'Twitter': None,
        'LinkedIn': None,
        'Instagram': None,
        'TikTok': None,
        'Pinterest': None,
        'YouTube': None
    }
    for link in soup.find_all('a', href=True):
        href = link['href']
        if 'facebook.com' in href:
            social_media['Facebook'] = href
        elif 'twitter.com' in href:
            social_media['Twitter'] = href
        elif 'linkedin.com' in href:
            social_media['LinkedIn'] = href
        elif 'instagram.com' in href:
            social_media['Instagram'] = href
        elif 'tiktok.com' in href:
            social_media['TikTok'] = href
        elif 'pinterest.com' in href:
            social_media['Pinterest'] = href
        elif 'youtube.com' in href:
            social_media['YouTube'] = href
    return social_media


def find_contact_pages_links(soup, base_url):
    contact_links = []
    for link in soup.find_all('a', href=True):
        if 'contact' in link.get_text().lower():
            contact_links.append(
                requests.compat.urljoin(base_url, link['href']))
    return contact_links


def extract_info_from_sub_pages(contact_links):
    emails = set()
    phones = set()
    email_pattern = re.compile(
        r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    phone_pattern = re.compile(
        r'\(?\b[0-9]{3}\)?[-. ]?[0-9]{3}[-. ]?[0-9]{4}\b')
    for link in contact_links:
        soup = fetch_and_parse_url(link)
        if soup:
            emails.update(re.findall(email_pattern, soup.text))
            phones.update(re.findall(phone_pattern, soup.text))
    return list(emails)[:1], list(phones)  # Limit to a single email


def extract_title(soup):
    if soup.title:
        return soup.title.string.strip()
    return None


def extract_meta_description(soup):
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag and 'content' in meta_tag.attrs:
        return meta_tag['content']
    return None

def scrape_website_data(url):
    # Import the global variable
    from app import stop_current_url
    
    soup = fetch_and_parse_url(url)
    if soup:
        # Check if we should stop
        if 'stop_current_url' in globals() and stop_current_url:
            return None
            
        domain = url.split("//")[-1].split("/")[0]
        base_url = f"http://{domain}"

        favicon_src = find_favicon(soup, base_url)
        contact_links = find_contact_pages_links(soup, base_url)
        
        # Check if we should stop before starting sub-page scraping
        if 'stop_current_url' in globals() and stop_current_url:
            return None
            
        emails, phones = extract_info_from_sub_pages(contact_links)
        social_media_links = find_social_media_links(soup)
        title = extract_title(soup)
        meta_description = extract_meta_description(soup)

        # Add all scraped data to a dictionary
        scraped_data = {
            'Website': url,
            'Title': title,
            'Meta Description': meta_description,
            'Contact Email': emails[0] if emails else None,
            'Contact Phone': ", ".join(phones) if phones else None,
            'Address': "Placeholder for address info",
            'Logo': favicon_src
        }

        scraped_data.update(social_media_links)
        return scraped_data
    else:
        return None


# Update the export_data_to_excel function to include only the meta description in the description column
def export_data_to_excel(data, filename="scraped_data.xlsx"):
    formatted_data = []
    for item in data:
        # Only include the meta description in the description column
        meta_description = item.get(
            "Meta Description", "No description available")

        formatted_data.append({
            "logo_src": item.get("Logo", ""),
            "profile_name": item.get("Title", "N/A"),
            "description": meta_description,  # Only meta description here
            "blog_link": item.get("Website", "#"),
            "facebook_link": item.get("Facebook", None),
            "twitter_link": item.get("Twitter", None),
            "linkedin_link": item.get("LinkedIn", None),
            "instagram_link": item.get("Instagram", None),
            "tiktok_link": item.get("TikTok", None),
            "pinterest_link": item.get("Pinterest", None),
            "youtube_link": item.get("YouTube", None),
            "email": item.get("Contact Email", "N/A"),
            "phone": item.get("Contact Phone", "N/A")
        })

    # Save the formatted data to an Excel file
    df = pd.DataFrame(formatted_data)
    df.to_excel(filename, index=False)
    print(f"Data exported to {filename}")
