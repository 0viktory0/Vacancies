from dotenv import load_dotenv
import os
import requests
from statistics import mean
from terminaltables import SingleTable


def predict_rub_salary_for_hh(vacancy_to_find, pages_count):
    hh_url = 'https://api.hh.ru/vacancies'
    vacancies_pages_result = []
    for page_number in range(pages_count):
        params = {'text': vacancy_to_find,
                  'area': 1,
                  'period': 30,
                  'per_page': 100,
                  'page': page_number}
        response = requests.get(hh_url, params=params)
        response.raise_for_status()
        vacancies_pages_result.append(response.json())
    vacancies_processed = 0
    vacancies_salary = []
    for vacancies_page in vacancies_pages_result:
        for vacancy in vacancies_page['items']:
            if vacancy['salary'] is not None:
                if vacancy['salary']['currency'] == "RUR":
                    if not vacancy['salary']['from']:
                        salary_from = 0
                    else:
                        salary_from = vacancy['salary']['from']
                    if not vacancy['salary']['to']:
                        salary_to = 0
                    else:
                        salary_to = vacancy['salary']['to']
                    vacancies_salary.append(get_average(salary_from, salary_to))
                    vacancies_processed += 1
    return vacancies_processed, int(mean(vacancies_salary))


def get_hh_statistic(languages):
    hh_total = []
    for language in languages:
        hh_url = 'https://api.hh.ru/vacancies'
        vacancy_to_find = f'программист {language}'
        params = {'text': vacancy_to_find,
                  'area': 1,
                  'period': 30,
                  'clusters': 'true',
                  'per_page': 0}
        response = requests.get(hh_url, params=params)
        response.raise_for_status()
        vacancies_found = response.json().get('found')
        vacancies_processed, average_salary = predict_rub_salary_for_hh(vacancy_to_find, pages_count=10)
        hh_total.append([language,
                         vacancies_found,
                         vacancies_processed,
                         average_salary])
    return(hh_total)


def get_average(salary_from, salary_to):
    if salary_from > 0 and salary_to > 0:
        average_salary = int((salary_from + salary_to) / 2)
    elif salary_from > 0:
        average_salary = int(salary_from * 1.2)
    elif salary_to > 0:
        average_salary = int(salary_to * 0.8)
    return average_salary


def predict_rub_salary_for_superJob(languages, secret_key):
    sj_url = 'https://api.superjob.ru/2.0/vacancies/'
    headers = {'X-Api-App-Id': secret_key}
    sj_total = []
    for language in languages:
        vacancy_to_find = f'программист {language}'
        params = {'keyword': vacancy_to_find,
                  'town': 'Москва',
                  'period': 30,
                  'count': 100}
        response = requests.get(sj_url, headers=headers, params=params)
        response.raise_for_status()
        average_salaries = []
        vacancies_processed = 0
        for item in response.json()['objects']:
            if (item['payment_from'] != 0 and item['payment_to'] != 0 and item['currency'] == 'rub'):
                vacancies_processed += 1
                average_salaries.append(get_average(item['payment_from'], item['payment_to']))
        if (response.json()['total'] != 0 and vacancies_processed != 0):
            sj_total.append([language,
                             response.json()['total'],
                             vacancies_processed,
                             int(mean(average_salaries))])
    return sj_total


def print_table(languages, title):
    rows = ['Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата']
    table_data = []
    table_data.append(rows)
    for language in languages:
        table_data.append(language)
    table = SingleTable(table_data, title)
    print(table.table)


def main():
    load_dotenv()
    secret_key = os.environ['SJ_TOKEN']
    languages = ['Python',
                 'Java',
                 'Javascript',
                 'С#',
                 'С++',
                 'PHP',
                 'Ruby',
                 'Kotlin']

    print_table(get_hh_statistic(languages), 'HeadHunter Moscow')
    print_table(predict_rub_salary_for_superJob(languages, secret_key), 'SuperJob Moscow')


if __name__ == '__main__':
    main()
