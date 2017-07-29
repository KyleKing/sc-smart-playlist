import time

import auth
import playlists
import requests
import utils
from bs4 import BeautifulSoup
from selenium import webdriver

lgr = utils.create_logger(__name__, "../tmp/__scraper.log", True)
# https://api.soundcloud.com/tracks/248646970?client_id=3115a25db758b44b4c3252342c4abcb7


class html_scraper(object):

    def __init__(self):
        """Get secret settings and check if scraper url parameter exists"""
        self.secret_config = auth.connect().secret()
        self.secret_url = hasattr(self.secret_config, "scraper_url")

    def fetch_html(self, mins=10):
        """Download the HTML file from the rendered scraper url webpage
            mins(int): time in minutes to attempt infinite scroll
        """
        if self.secret_url:
            driver = webdriver.PhantomJS()
            driver.set_window_size(1440, 900)
            driver.get(self.secret_config["scraper_url"])
            # Hard code a timeout
            timeout = time.time() + 60 * int(mins)
            print "start scroll: " + time.asctime(time.localtime(time.time()))
            while True:
                driver.execute_script(
                    "window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(0.5)
                if time.time() > timeout:
                    print "end: " + time.asctime(time.localtime(time.time()))
                    break
            # Save HTML
            html = driver.page_source
            open("../tmp/scraped_html.html", "w").write(html).close()
            # driver.save_screenshot("3_home_page.png")
            driver.close()

        # # WIP: Log in to SoundCloud with Selenium
        # username = self.secret_config["username"]
        # password = self.secret_config["password"]
        # driver.get("https://soundcloud.com/signin")

        # # # Complete the sign in form
        # username_input = driver.find_elements_by_xpath(
        #     "//*[@id="content"]/div/div/div[1]/form/div/div[1]/div/div[2]/div/input")[0]
        # username_input.send_keys(username)
        # submit_button = driver.find_elements_by_xpath(
        #     "//*[@id="content"]/div/div/div[1]/form/div/div[1]/div/button")[0]
        # submit_button.click()
        # driver.save_screenshot("../tmp/1_sign_in.png")
        # time.sleep(5)

        # pass_input = driver.find_elements_by_xpath(
        #     "//*[@id="content"]/div/div/div[1]/form/div/div[2]/div/div[2]/div/input")
        # lgr.debug(pass_input)
        # html = driver.page_source
        # lgr.debug(html)
        # # email_input.send_keys(password)
        # # ^Can"t enter my password - field is "inactive"?
        # submit_button = driver.find_elements_by_xpath(
        #     "//*[@id="content"]/div/div/div[1]/form/div/div[2]/div/button")[0]
        # submit_button.click()
        # driver.save_screenshot("2-1_pass.png")
        # time.sleep(5)

    def parse_html(self, fn):
        """Parse downloaded HTML file for track information
            fn (str): path to HTML file
        """
        with open(fn) as filehandle:
            soup = BeautifulSoup(filehandle, "html.parser")
            for match in soup.find_all("a", class_="soundTitle__title"):
                # lgr.debug(match.prettify())
                href = match["href"]
                uri = "/resolve?url=http://soundcloud.com{}".format(href)
                # FIXME: Inconsistent various HTTP errors (401 and 403)
                try:
                    resp = playlists.generate().get(uri).__dict__["obj"]
                    lgr.debug(resp)
                    lgr.debug("Resp: {}-for-{}\n".format(resp["id"], href))
                except (requests.exceptions.HTTPError) as err:
                    lgr.debug("Failed ({}): {} [{}]\n".format(err, err.errno, err.strerror, uri))

                time.sleep(0.1)


# http://api.soundcloud.com/resolve?url=http://soundcloud.com/matas/hobnotropic&client_id=3115a25db758b44b4c3252342c4abcb7


if __name__ == "__main__":
    # # Fetch the HTML file for the scraper_url
    # html_scraper().fetch_html(1)

    # Test parsing an HTML file
    html_scraper().parse_html("../tmp/reposts.html")
    # html_scraper().parse_html("../tmp/full_html.html")
