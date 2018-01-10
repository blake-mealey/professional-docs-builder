# Resume Builder

Handles the downloading of JSON data files from a private GitHub repo, the generation of .tex files from the data files, the compilation of the resulting TeX document using LuaLaTeX, and the managing and uploading of the resulting PDF documents. Every variable option defaults to the value of the same key in config.json. For example, if the --engine option is not included, then the program will use the 'engine' entry in the dictionary stored in config.json.

```
	python3 compile.py --help | less
```