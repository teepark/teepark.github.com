For the last couple of hours I have been hacking together a publishing mechanism, but it's not quite the blogging engine that we are all so used to.

Now I, like every other python developer out there who has ever heard of django, have written my own blogging engine in it a couple of times, and played around with a couple of the more popular ones. With django I've done pingback and metaweblog via xmlrpc, a custom comment stack, facebook, flickr, and twitter integration, and a lot more. It's great.

**My requirements:**

- No $, so no purchasing hosting
- No hosting my own webserver
- No blogger
- No google pages
- No xanga
- No livejournal
- ...you get the idea

But this time, constrained by the requirements above, I wasn't going to be able to do those things. Django needs real hosting, and my free options are pretty much one of the custom hosted blog systems above (all of which I have tried and don't like), or having my free hosting just serve static files.

I chose the latter, and the free hosting service I'm using for that is github's pages. Which is especially nice, because my github profile is not a bad center for my online identity. By using github pages, the url for my blog is <http://teepark.github.com> (not half bad), and all I have to do to update it is push my github repository named "[teepark.github.com][]".

No, I'm not just writing HTML by hand to create blog posts. The technologies I'm using are just mako for templating, markdown for my entry format, and of course git for the uploading.

[The site content generation script](http://github.com/teepark/teepark.github.com/blob/master/generate.py) searches for *.markdown files in the src/ directory, converts that markdown to html 4 and passes it into mako running the [entry.html][] template (also using the last-modified date and figuring the post title from the filename), and generates an HTML file for each entry in the entries/ directory (actually in subdirectories determined by the last-modified date, to create date-based urls). It also collects a brief excerpt of each entry using truncate_html_words() poached from django.utils.text, sorts them by date and passes them into the [index.html][] template.

The great thing about all this is that I have found that I can do a pretty good job integrating with web services and having dynamic elements on my page entirely with javascript. So far I have data from github (via [Dr Nic's github badge](http://github.com/drnic/github-badges)), twitter (with their javascript embed), and even powerful comments on my posts from [disqus][]. I'm pretty stoked about what can be done totally server-less.

Now to see if I update this thing at all. I have a couple of ideas for posts, but that does not a successful blogging endeavor make.

[teepark.github.com]: http://github.com/teepark/teepark.github.com  "The git repository driving this site"
[index.html]: http://github.com/teepark/teepark.github.com/blob/master/templates/index.html
[entry.html]: http://github.com/teepark/teepark.github.com/blob/master/templates/entry.html
[disqus]: http://disqus.com
