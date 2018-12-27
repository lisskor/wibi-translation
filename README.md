# wibi_translation

This is an attempt at translating the WiBi Wikipedia bitaxonomy.

## get_sentences.py

This script will search Yandex for words of each line of given file. Titles, headlines and passages
will be extracted from the search result. The resulting file will have one list of extracted texts in JSON format per line,
corresponding to lines of the original file. To perform the search, a Yandex username and a key provided by Yandex at
[Yandex.XML settings](https://xml.yandex.com/settings/ "Yandex XML settings")
is needed. Search type needs to be set to 'Worldwide', and the correct current IP has to be selected.

### Usage

`python get_sentences.py -t taxonomyfile -o outputfile -u username -k key`
