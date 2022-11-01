# aber-module-scrape
 
This project is a sister to *aber-browser-extension-main*.

I realized that the aber browser extension needed to preload its data to increase speed so this code is designed to scrape the Aberystwyth module website and combine the data into a more friendly dictionary that the extension can parse. It is designed to be run autonomously every ~month on a server and then served through http.

*NOTE: This has not been tested since 2021, contains no network throttling contingency so you may get IP banned or something.*