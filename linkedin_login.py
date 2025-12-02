from playwright.sync_api import sync_playwright
import os
import sys
import json
import csv
import re
import time
import traceback
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
 
PHONE_NUMBER = """Give your phone number here"""
PASSWORD = """Give your password here"""
SEARCH_TERM = "vendor empanelment"

# ----------------- paste this function into linkedin_login.py -----------------

def safe_text(locator, timeout=200):
    """Return inner_text safely. Never throws. Never hangs."""
    try:
        if locator.count() == 0:
            return None
        return locator.first.inner_text(timeout=timeout).strip()
    except Exception:
        return None

# improved email regex
_EMAIL_RE = re.compile(r"[a-zA-Z0-9.+-_]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
# improved phone regex: matches +country and common formats, 7-16 digits
_PHONE_RE = re.compile(r"(\+?\d{1,3}[\s\-\.]?)?(\(?\d{3,4}\)?[\s\-\.]?)?[\d\s\-\.]{6,15}")

# heuristic location keywords (extend as needed)
_LOCATION_KEYWORDS = [
    "Hyderabad","Bengaluru","Bangalore","Chennai","Mumbai","Delhi",
    "Kolkata","Pune","India","USA","United Kingdom","UK","Dubai","Noida",
    "Gurgaon","Bengaluru","Bengaluru"
]

def clean_text(text):
    """Cleans up the extracted post text."""
    if not text:
        return None
    # Remove "...see more" and similar phrases
    text = re.sub(r'…\s*more$', '', text).strip()
    # Replace multiple newlines/spaces with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def extract_email(text):
    if not text:
        return None
    m = _EMAIL_RE.search(text)
    return m.group(0) if m else None

def extract_phone(text):
    if not text:
        return None
    m = _PHONE_RE.search(text)
    if not m:
        return None
    phone = m.group(0)
    # clean whitespace
    phone = re.sub(r"[^\d+]", "", phone)
    # basic length check
    if len(re.sub(r"[^\d]", "", phone)) < 7:
        return None
    return phone

def extract_location(text):
    if not text:
        return None
    low = text.lower()
    for k in _LOCATION_KEYWORDS:
        if k.lower() in low:
            return k
    return None

# ---- MAIN EXTRACTOR ----
def extract_posts_from_page(page, out_csv_path="results.csv", debug_html="debug_page_source.html"):
    """Extract LinkedIn posts to CSV with columns: name,email,phone_number,location,url,text"""
    # let feed finish rendering
    try:
        page.wait_for_timeout(1500)
    except Exception:
        pass

    posts = page.locator("div[role='article']")
    try:
        total = posts.count()
    except Exception:
        total = 0

    if total == 0:
        # debug snapshot
        try:
            with open(debug_html, "w", encoding="utf-8") as f:
                f.write(page.content())
            print(f"DEBUG: No posts found. Dumped page to {debug_html}")
        except Exception:
            pass
        return []

    print(f"Found {total} posts. Extracting...")

    results = []
    for i in range(total):
        print(f" → Post {i+1}/{total}")
        try:
            post = posts.nth(i)

            # author name
            author = None
            try:
                author = safe_text(post.locator("span.feed-shared-actor__name")) or safe_text(post.locator(".feed-shared-actor__name"))
            except Exception:
                author = None

            # post text - try several selectors
            body = None
            for sel in [
                "div.feed-shared-text__text-view",
                "div.update-components-text",
                "span.break-words",
                "div[dir='ltr'] p",
                "p"
            ]:
                try:
                    txt = safe_text(post.locator(sel))
                    if txt and len(txt) > 2:
                        body = txt
                        break
                except Exception:
                    continue

            # expand 'see more' if present (best-effort)
            try:
                see_more = post.locator("button:has-text('see more'), button[aria-label='see more']")
                if see_more.count():
                    for s in range(see_more.count()):
                        try:
                            see_more.nth(s).click(timeout=200)
                        except Exception:
                            pass
                    # re-read body
                    for sel in [
                        "div.feed-shared-text__text-view",
                        "div.update-components-text",
                        "span.break-words",
                        "div[dir='ltr'] p",
                    ]:
                        try:
                            txt = safe_text(post.locator(sel))
                            if txt and len(txt) > 2:
                                body = txt
                                break
                        except Exception:
                            continue
            except Exception:
                pass

            # permalink detection
            link = None
            try:
                anchors = post.locator("a")
                for j in range(anchors.count()):
                    try:
                        href = anchors.nth(j).get_attribute("href")
                        if href and ("/posts/" in href or "/feed/update/" in href or "/activity/" in href or "/detail/" in href):
                            link = href
                            break
                    except Exception:
                        continue
                if not link and anchors.count():
                    link = anchors.nth(0).get_attribute("href")
            except Exception:
                link = None

            # extract email / phone / location from body text (if present)
            email = extract_email(body) or None
            phone = extract_phone(body) or None
            location = extract_location(body) or None

            # Clean the body text before saving
            cleaned_body = clean_text(body)

            results.append({
                "name": author or "",
                "email": email or "",
                "phone_number": phone or "",
                "location": location or "",
                "url": link or "",
                "text": cleaned_body or ""
            })

        except Exception as e:
            print(f"ERROR processing post {i+1}: {e}")
            traceback.print_exc()
            continue

    # write CSV
    try:
        with open(out_csv_path, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["name", "email", "phone_number", "location", "url", "text"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        print(f"✅ Saved {len(results)} posts to {out_csv_path}")
    except Exception as e:
        print("Failed to write CSV:", e)
        traceback.print_exc()

    return results

def run():
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=50)
            context = browser.new_context(viewport={"width": 1280, "height": 1024})
            page = context.new_page()

            try:
                # 1. Go to LinkedIn login page
                page.goto("https://www.linkedin.com/login")

                # 2. Login with phone + password
                print("Logging in...")
                page.fill('input[name="session_key"]', PHONE_NUMBER)
                page.fill('input[name="session_password"]', PASSWORD)
                page.get_by_role("button", name="Sign in", exact=True).click()

                # 3. Wait for page to load after login
                # We check for either the feed search box or a checkpoint page.
                page.wait_for_selector('input[placeholder="Search"], #captcha-internal', timeout=90000)
                print("Login submitted. Current URL:", page.url)

                # 4. If LinkedIn shows checkpoint / captcha
                if "checkpoint" in page.url:
                    print("\nLinkedIn has sent you to a checkpoint / captcha page.")
                    print("You MUST solve it manually in the opened browser window.")
                    input("After you finish the captcha/verification and reach your feed, press ENTER here... ")

                    # Wait for the feed to appear after solving the checkpoint
                    page.wait_for_selector('input[placeholder="Search"]', timeout=90000)
                    print("URL after solving checkpoint:", page.url)

                # 5. At this point, you should be logged in (ideally on /feed)
                print("Login successful or checkpoint passed.")

                # Ensure we are on the feed page before continuing
                if "/feed" not in page.url:
                    print("Not on the feed page, navigating to it...")
                    page.goto("https://www.linkedin.com/feed/")
                    page.wait_for_selector('input[placeholder="Search"]', timeout=60000)

                # 6. Try to close popups (best-effort only)
                try:
                    page.locator('button:has-text("Accept")').first.click(timeout=3000)
                except:
                    pass

                try:
                    page.locator('button:has-text("Skip")').first.click(timeout=3000)
                except:
                    pass

                # 7. Search for vendor empanelment
                try:
                    search_box = page.get_by_role("combobox", name="Search")
                    search_box.click()
                    search_box.fill(SEARCH_TERM)
                    page.keyboard.press("Enter")

                    # Wait for search results to appear
                    page.wait_for_selector('h1:has-text("Search results")', timeout=60000)
                    print("Search completed. URL:", page.url)
                except Exception as e:
                    print("Could not perform search automatically:", e)
                    return

                # 8. Filter by "Posts"
                print("Filtering by Posts...")
                page.get_by_role("button", name="Posts", exact=True).click()
                # Wait for the search results to update to posts
                page.wait_for_url("**/search/results/content/**", timeout=60000)
                print("Filtered by Posts.")

                # 9. Sort by "Recent" (using the new "Date posted" filter)
                print("Sorting by most recent...")
                try:
                    # Click the "Date posted" dropdown
                    # Wait explicitly for the button to be visible before clicking
                    date_posted_button = page.get_by_role("button", name="Date posted", exact=True)
                    date_posted_button.wait_for(state="visible", timeout=15000)
                    page.get_by_role("button", name="Date posted", exact=True).click()
                    # Click the "Past 24 hours" option for most recent
                    page.get_by_role("radio", name="Past 24 hours").locator("..").click()
                    # Click the "Show results" button to apply the filter
                    page.get_by_role("button", name="Show results", exact=True).click()
                    # Wait for the page to reload with the sorted results
                    page.wait_for_load_state("networkidle", timeout=60000)
                    print("Sorted by most recent posts.")
                except Exception as e:
                    print(f"Could not sort by recent, proceeding with default sort. Error: {e}")

                # 10. Scroll down to load more posts
                print("Scrolling to load more posts...")
                last_height = page.evaluate("document.body.scrollHeight")
                for i in range(500): # Scroll 500 times
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    print(f"Scrolled {i+1}/500...")
                    page.wait_for_timeout(3500) # Wait for content to load
                    new_height = page.evaluate("document.body.scrollHeight")
                    if new_height == last_height:
                        print("Reached end of scroll results.")
                        break
                    last_height = new_height

                # 11. Scrape the data from posts
                print("Scrolling done — now extracting posts")
                posts = extract_posts_from_page(page, out_csv_path="linkedin_data.csv")
                print("Extraction complete. Posts count:", len(posts))

                # 13. Keep browser open
                input("Press ENTER to close browser...")
                
            finally:
                browser.close()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    run()
