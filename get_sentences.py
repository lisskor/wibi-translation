#!/usr/bin/env python3

import json
import re
import html
import argparse
import logging
from xml.etree import ElementTree

import requests


# Configure logging
logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
                    datefmt='%m/%d/%Y %I:%M:%S %p', level=logging.INFO)


def get_lines_from_file(taxonomy_filename):
    """
    Yield a generator of one list of words
    (separable by tabs and spaces) per line of file.

    :param taxonomy_filename: path to taxonomy file
    :return: generator of word lists
    """
    with open(taxonomy_filename, 'r', encoding='utf-8') as tax_fh:
        for line in tax_fh:
            words = [x for x in re.split('[ \t]', line.strip()) if x]
            yield words
            

def query_from_wordlist(wordlist):
    """
    Make query from a list of words by adding a '+' before each word
    and joining them by spaces ('+' means that the word has to be present
    in relevant documents).

    :param wordlist: list of words to search for
    :return: query for Yandex search ('+word0 +word1 ...')
    """
    return ' '.join(['+' + word for word in wordlist])


def search(query, user, key):
    """
    Search Yandex for a given query, return the contents
    of the response or, if the request failed, the status code.

    :param query: query to search for
    :param user: Yandex username
    :param key: key provided by Yandex
    :return: response contents or an error message
    """
    data = {'l10n': 'en', 'user': user,
            'key': key, 'text': query}
    response = requests.get("https://yandex.com/search/xml", params=data)
    if response.status_code == 200:
        return response.content
    else:
        return response.status_code
    

def gettext(elem):
    """
    Return all internal text contents of an ElementTree element.

    :param elem: tree element
    :return: text of the element (string)
    """
    text = elem.text or ""
    for subelem in elem:
        text = text + gettext(subelem)
        if subelem.tail:
            text = text + subelem.tail
    return text


def get_all_passages(tree):
    """
    Return a list of all titles, headlines and passages
    found by Yandex search whose language is marked as English.

    :param tree: content of a Yandex search response
    parsed into an ElementTree
    :return: list of all titles, headlines and passages in the response
    """
    
    passages = []
    
    for doc in tree.iter('doc'):
        for element in doc.iter():
            # Need only titles, headlines and 'passages'.
            if element.tag in ['title', 'headline', 'passage']:
                if [elem.text for elem in doc.iter('lang')]:
                    # Check that language is marked as English.
                    if [elem.text for elem in doc.iter('lang')][0] == 'en':
                        passages.append(html.unescape(gettext(element)))
                
    return passages


def write_passages(taxonomy_filename, output_filename, user, key):
    """
    For each line in taxonomy_filename, search Yandex
    for documents containing all words in the line,
    and write to output_filename all headlines, titles and passages found.

    :param taxonomy_filename: path to taxonomy file
    :param output_filename: path to output file
    :param user: Yandex username
    :param key: key provided by Yandex
    :return: None
    """
    # Get a generator of one list of words per line.
    words_generator = get_lines_from_file(taxonomy_filename)

    with open(output_filename, 'w', encoding='utf-8') as result_fh:

        logging.info('Searching Yandex for lines of {}'.
                     format(taxonomy_filename))
        logging.info('Writing results into {}'. format(output_filename))

        for i, word_list in enumerate(words_generator):
            # Send request to Yandex,
            # save response if request successful
            # or status code otherwise.
            response = search(query=query_from_wordlist(word_list),
                              user=user, key=key)

            # Check that request was successful,
            # report an error and exit otherwise.
            if type(response) is int:
                logging.error('Request for line {} failed, status code {}'.
                              format(i+1, response))
                logging.info('Exiting')
                return

            # Parse contents of response into an ElementTree.
            tree = ElementTree.fromstring(response)

            # Check that the search was successful,
            # report an error and exit otherwise.
            if 'error' in [element.tag for element in tree.iter()]:
                error_message = [elem.text for elem in tree.iter('error')][0]
                logging.error('An error occurred at line {}: {}'.
                              format(i+1, error_message))
                logging.info('Exiting')
                return

            # Extract titles, headlines and passages from the response.
            passages = get_all_passages(tree)
            # Write results into output file.
            result_fh.write(json.dumps(passages, ensure_ascii=False)+'\n')

            # Report progress.
            if i % 1000 == 0:
                logging.info('Processed {} lines'.format(i))

    logging.info('Done')


def parse_cmd_arguments():
    """
    Parse command line arguments.

    :return: parsed arguments namespace
    """
    descr = """
    Taxonomy searching file.
    
    This module takes a taxonomy file and searches Yandex
    for words of each line of given file. Titles, headlines and passages
    will be extracted from the search result. The resulting file
    will have one list of extracted texts in JSON format per line,
    corresponding to lines of the original file. To perform the search,
    a Yandex username and a key provided by Yandex at
    https://xml.yandex.com/settings/ is needed. Search type needs
    to be set to 'Worldwide', and the correct current IP has to be selected.
    """

    parser = argparse.ArgumentParser(description=descr)
    parser.add_argument('-t', '--taxonomy',
                        help='input taxonomy file',
                        required=True)
    parser.add_argument('-o', '--output',
                        help='output file to write search results into',
                        required=True)
    parser.add_argument('-u', '--username',
                        help='Yandex username',
                        required=True)
    parser.add_argument('-k', '--key',
                        help='key provided by Yandex',
                        required=True)

    cmd_args = parser.parse_args()
    return cmd_args


if __name__ == '__main__':
    args = parse_cmd_arguments()
    write_passages(taxonomy_filename=args.taxonomy,
                   output_filename=args.output,
                   user=args.username, key=args.key)
