This repository is my attempt at a very simple time series database to meet my specific needs.

As described in the README, these are the principles:

- I only need second precision
- It's only a simple string lookup by name
- I'm only querying by days at a time
- Concurrent traffic is extremely low
- Compression has to just be "good" enough
- Data is normally appended
- Data usually has the same daily time pattern, like on 10 minute intervals

I am not a database expert or developer so keep that in mind when taking my suggestions.
Please offer strong criticism and questioning on everything I ask.

We can prototype in something like Python, but ultimately want it to have the highest performance using something like C or zig.
