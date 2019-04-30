# Maciej Mikuła usosweb scraper.
# Gathers data about courses at University of Warsaw, Faculty of Mathematics, Informatics and Mechanics.
# Data is saved into json file.

from bs4 import BeautifulSoup
import requests
import re
import json


def get_course_id(soup):
    return soup.find('td', text=re.compile('Kod przedmiotu:')).findNext('td').text


def get_erasmus_code(soup):
    try:
        return soup.find('td', text=re.compile('Kod Erasmus / ISCED:')).findNext('td').text.split('/')[0].strip()
    except AttributeError:
        return ""


def get_isced(soup):
    try:
        return soup.find('td', text=re.compile('Kod Erasmus / ISCED:')).findNext('td').text.split('/')[1].strip()
    except AttributeError:
        return ""


def get_course_title(soup):
    return soup.find('td', text=re.compile('Nazwa przedmiotu:')).findNext('td').text


def get_groups(soup):
    try:
        return soup.find('td', text=re.compile('Grupy:')).findNext('td').text.strip().split('\n')
    except AttributeError:
        return ""


def get_ects_points(soup):
    try:
        return soup.find('td', text=re.compile('Punkty ECTS i inne:')).findNext('td').text.strip().split('\n')[0].strip()
    except AttributeError:
        return ""


def get_language(soup):
    try:
        return soup.find('td', text=re.compile('Język prowadzenia:')).findNext('td').text.strip()
    except AttributeError:
        return ""


def get_type_of_course(soup):
    try:
        return soup.find('td', text=re.compile('Rodzaj przedmiotu:')).findNext('td').text.strip()
    except AttributeError:
        return ""


def get_requirements(soup):
    try:
        return [require_subject.text for require_subject in soup.find('td', text=re.compile('Wymagania')).findNext('td').find_all('a')]
    except AttributeError:
        return ""


def get_short_description(soup):
    try:
        return soup.find('td', text=re.compile('Skrócony opis:')).findNext('td').text.strip()
    except AttributeError:
        return ""


def get_full_description(soup):
    try:
        return soup.find('td', text=re.compile('Pełny opis:')).findNext('td').text.strip()
    except AttributeError:
        return ""


def get_bibliography(soup):
    try:
        return soup.find('td', text=re.compile('Literatura:')).findNext('td').text.strip()
    except AttributeError:
        return ""


def get_learning_outcomes(soup):
    try:
        return soup.find('td', text=re.compile('Efekty kształcenia:')).findNext('td').text.strip().replace('\n', ' ')
    except AttributeError:
        return ""


def get_assessment_info(soup):
    try:
        return soup.find('td', text=re.compile('Metody i kryteria oceniania:')).findNext('td').text.strip()
    except AttributeError:
        return ""


def get_classes_period(soup):
    try:
        return 'zimowy' if 'zimowy' in soup.find('i', text=re.compile('Semestr')).text.strip() else 'letni'
    except AttributeError:
        return ""


def get_types_of_classes(soup):
    try:
        return [class_type.strip() for class_type in soup.find('td', text=re.compile('Typ zajęć:')).findNext('td').text.strip().split('więcej informacji')][:-1]
    except AttributeError:
        return ""


def get_coordinators(soup):
    try:
        return soup.find('td', text=re.compile('Koordynatorzy:')).findNext('td').text.strip().split('\n')
    except AttributeError:
        return ""


def get_group_instructors(soup):
    try:
        return [instructor.strip() for instructor in soup.find('td', text=re.compile('Prowadzący grup:')).findNext('td').text.split(',')]
    except AttributeError:
        return ""


def get_course_data(url):
    """ Collects course data
            :return: course's code, dictionary with information about the course
    """
    data = {}
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')

    course_code = get_course_id(soup)
    data['erasmus_code'] = get_erasmus_code(soup)
    data['ISCED'] = get_isced(soup)
    data['name'] = get_course_title(soup)
    data['groups'] = get_groups(soup)
    data['ects'] = get_ects_points(soup)
    data['language'] = get_language(soup)
    data['type_of_course'] = get_type_of_course(soup)
    data['requirements'] = get_requirements(soup)
    data['short_description'] = get_short_description(soup)
    data['full_description'] = get_full_description(soup)
    data['bibliography'] = get_bibliography(soup)
    data['learning_outcomes'] = get_learning_outcomes(soup)
    data['assessment_info'] = get_assessment_info(soup)
    data['period'] = get_classes_period(soup)
    data['types_of_classes'] = get_types_of_classes(soup)
    data['coordinators'] = get_coordinators(soup)
    data['group_instructors'] = get_group_instructors(soup)

    return course_code, data


def generate_courses_urls_list(soup):
    """ Generates list of courses' urls to visit - every url represents one course """
    return [anchor['href'] for anchor in soup.find_all('a', 'wrblue')]


def collect_courses_data(url, data):
    """ Collects data about all subjects from given url - url contains list of courses
        Appends data to given dict
    """
    soup = BeautifulSoup(requests.get(url).content, 'html.parser')
    courses_urls = generate_courses_urls_list(soup)

    for course_url in courses_urls:
        course_code, course_data = get_course_data(course_url)
        data[course_code] = course_data


def collect_all_courses_data(urls_list):
    data = {}

    for url in urls_list:
        collect_courses_data(url, data)
        print("data shard collected")

    return data


def generate_list_of_urls_with_listed_courses(url_start):
    """ Generates list of urls to visit - every url contains different list of courses """
    met_offsets = set()
    urls_to_visit = set()
    urls_to_visit.add(url_start)

    pages_list = []

    while len(urls_to_visit) > 0:
        curr_url = urls_to_visit.pop()
        soup = BeautifulSoup(requests.get(curr_url).content, 'html.parser')

        anchors = soup.find('td', 'wrnavbar').parent.find_all('a')
        for anchor in anchors:
            offset = int(re.search(r'(offset=)(\d+)', anchor['href']).groups()[1])
            if offset not in met_offsets:
                met_offsets.add(offset)
                urls_to_visit.add(anchor['href'])
                pages_list.append(anchor['href'])

    return pages_list


def main():
    url_start = 'https://usosweb.mimuw.edu.pl/kontroler.php?_action=katalog2/przedmioty/szukajPrzedmiotu&cp_showDescriptions=0&cp_' \
               'showGroupsColumn=0&cp_cdydsDisplayLevel=2&f_tylkoWRejestracji=0&f_obcojezyczne=0&method=faculty_organized&kieruj' \
               'NaPlanyGrupy=0&jed_org_kod=10000000&tabd196_offset=0&tabd196_limit=30&tabd196_order=2a1a'

    urls_list = generate_list_of_urls_with_listed_courses(url_start)
    data = collect_all_courses_data(urls_list)
    with open('./courses.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)


main()
