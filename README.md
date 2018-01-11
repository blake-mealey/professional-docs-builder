# Professional Document Builder

Used to produce resume and cover letter PDFs from JSON data files. Also handles the uploading of specific PDFs to desired sites. I use this in conjunction with my [resume-site](https://github.com/blake-mealey/resume-site) repo which generates a web page using the same JSON data files. I also use the upload functionality to upload the latest PDF version of my resume to that same site. Currently under reconstruction and generalization to better support cover letters alongside resumes and to make this less specific to myself.

To try and use this for yourself, clone the repo and run:

```
python3 compile.py --help | less
```

Note that some of the required setup is undocumented, and also under construction so attempt at your own peril for now.
