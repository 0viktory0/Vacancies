from dotenv import load_dotenv
import os
import requests
from statistics import mean
from terminaltables import SingleTable


def get_vacancies_hh_pages_result(vacancy_to_find, hh_area_code, searching_period):
    hh_url = 'https://api.hh.ru/vacancies'
    vacancies_pages_result = []
    count_pages = 10
    for page_number in range(count_pages):
        params = {'text': vacancy_to_find,
                  'area': hh_area_code,
                  'period': searching_period,
                  'page': page_number}
        response = requests.get(hh_url, params=params)
        response.raise_for_status()
        vacancies_pages_result.append(response.json())
    return vacancies_pages_result


def predict_rub_salary_for_hh(vacancy_to_find, hh_area_code, searching_period):
    processed_vacancies = 0
    vacancies_salary = []
    for vacancies_page in get_vacancies_hh_pages_result(vacancy_to_find, hh_area_code, searching_period):
        for vacancy in vacancies_page['items']:
            if vacancy['salary'] and vacancy['salary']['currency'] == "RUR":
                salary_from = vacancy['salary']['from'] or 0
                salary_to = vacancy['salary']['to'] or 0
                vacancies_salary.append(get_average(salary_from, salary_to))
                processed_vacancies += 1
    return processed_vacancies, int(mean(vacancies_salary))


def get_hh_statistic(languages, hh_area_code, searching_period):
    hh_total = []
    for language in languages:
        hh_url = 'https://api.hh.ru/vacancies'
        vacancy_to_find = f'программист {language}'
        params = {'text': vacancy_to_find,
                  'area': hh_area_code,
                  'period': searching_period,
                  'clusters': 'true',
                  'per_page': 0}
        response = requests.get(hh_url, params=params)
        response.raise_for_status()
        found_vacancies = response.json().get('found')
        processed_vacancies, average_salary = predict_rub_salary_for_hh(vacancy_to_find, hh_area_code, searching_period)
        hh_total.append([language,
                         found_vacancies,
                         processed_vacancies,
                         average_salary])
    return hh_total


def get_average(salary_from, salary_to):
    if salary_from and salary_to:
        average_salary = int((salary_from + salary_to) / 2)
    elif salary_from:
        average_salary = int(salary_from * 1.2)
    elif salary_to:
        average_salary = int(salary_to * 0.8)
    return average_salary


def get_all_vacancies_sj(secret_key, language):
    page = 0
    pages_number = 1
    header = {'X-Api-App-Id': secret_key}
    while page < pages_number:
        params = {'town':'Москва',
                  'keyword': f'программист {language}',
                  'page': page}
        response = requests.get('https://api.superjob.ru/2.0/vacancies/', headers=header, params=params)
        response.raise_for_status()
        page += 1
        pages_number += 1
        all_vacancies = response.json()
        return all_vacancies


def get_salaries_sj(all_vacancies):
    processed_vacancies = 0
    predicted_salaries = []
    for vacancy_salary in all_vacancies['objects']:
        if vacancy_salary['currency'] != 'rub':
            continue
        salary_from = vacancy_salary['payment_from'] or 0
        salary_to = vacancy_salary['payment_to'] or 0
        predicted_salaries.append(get_average(salary_from, salary_to))
        processed_vacancies += 1
    return processed_vacancies, int(mean(predicted_salaries))


def get_sj_statistic(languages, secret_key):
    sj_total = []
    for language in languages:
        all_vacancies_sj = get_all_vacancies_sj(secret_key, language)
        processed_vacancies, average_salary = get_salaries_sj(all_vacancies_sj)
        sj_total.append([language,
                         get_all_vacancies_sj(secret_key, language)['total'],
                         processed_vacancies,
                         average_salary])
    return sj_total


def print_table(languages, title):
    rows = ['Язык программирования',
            'Вакансий найдено',
            'Вакансий обработано',
            'Средняя зарплата']
    table = []
    table.append(rows)
    for language in languages:
        table.append(language)
    salaries_table = SingleTable(table, title)
    print(salaries_table.table)


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
    hh_area_code = 1
    searching_period = 30
    print_table(get_hh_statistic(languages, hh_area_code, searching_period), 'HeadHunter Moscow')
    print_table(get_sj_statistic(languages, secret_key), 'SuperJob Moscow')


if __name__ == '__main__':
    main()