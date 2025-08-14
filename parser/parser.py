"""
Упрощенный парсер ИТМО с автоматическим скачиванием PDF
"""

import json
import logging
import time
from pathlib import Path
from urllib.parse import urlparse
import os

import PyPDF2
import requests
from bs4 import BeautifulSoup


class ITMOParser:
    def __init__(self):
        self.base_dir = Path(__file__).parent  # Папка parser/
        self.data_dir = self.base_dir.parent / "data"  # Папка data/
        self.pdf_dir = self.data_dir / "downloaded_pdfs"
        self.data_dir.mkdir(exist_ok=True)
        self.pdf_dir.mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

        logging.basicConfig(
            level=logging.INFO,
            format='%(message)s',
            handlers=[logging.FileHandler(self.base_dir / 'parser.log', encoding='utf-8')]
        )
        self.logger = logging.getLogger(__name__)

        self.programs = {
            "Искусственный интеллект": "https://abit.itmo.ru/program/master/ai",
            "Управление ИИ-продуктами": "https://abit.itmo.ru/program/master/ai_product"
        }

    def get_page(self, url):
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            self.logger.error(f"Ошибка загрузки {url}: {e}")
            return None

    def extract_json_data(self, soup):
        try:
            script = soup.find('script', {'id': '__NEXT_DATA__'})
            if script:
                return json.loads(script.string).get('props', {}).get('pageProps', {})
        except:
            pass
        return {}

    def parse_basic_info(self, soup):
        data = {}

        # Программы
        programs = {}
        for item in soup.find_all('div', class_='Directions_table__item__206L0'):
            name_elem = item.find('h5', class_='Directions_table__name__CklG5')
            if name_elem:
                name = name_elem.get_text(strip=True)
                places = []
                for place in item.find_all('div', class_='Directions_table__places__RWYBT'):
                    span = place.find('span')
                    p = place.find('p')
                    if span and p:
                        places.append(f"{span.get_text(strip=True)} {p.get_text(strip=True).lower()}")
                programs[name] = ', '.join(places)
        data['Реализуемые программы'] = programs

        # Описание
        about = soup.find('div', class_='AboutProgram_aboutProgram__textWrapper___j1KQ')
        if about:
            data['Описание программы'] = about.get_text(strip=True)

        # Карьера
        career = soup.find('div', class_='Career_career__container___st5X')
        if career:
            data['Карьера'] = career.get_text(strip=True)

        return data

    def parse_faq(self, soup):
        faq = {}
        questions = soup.find_all('div', class_='Accordion_accordion__title__tSP_0')
        answers = soup.find_all('div', class_='Accordion_accordion__item__A6W5t')

        for q, a in zip(questions, answers):
            faq[q.get_text(strip=True)] = a.get_text(strip=True)

        return faq

    def parse_enhanced_info(self, json_data):
        data = {}

        # API данные
        api_program = json_data.get('apiProgram', {})
        if api_program:
            data['Код направления'] = api_program.get('direction_code')
            data['Направление образования'] = api_program.get('direction_of_education')
            data['Учебный план (PDF)'] = api_program.get('academic_plan')
            data['Имеет аккредитацию'] = api_program.get('hasAccreditation', False)
            data['Военная кафедра'] = api_program.get('isMilitary', False)

            study = api_program.get('study', {})
            if study:
                data['Период обучения'] = study.get('label')
                data['Форма обучения'] = study.get('mode')

            cost = api_program.get('educationCost', {})
            if cost:
                data['Стоимость для россиян'] = cost.get('russian')
                data['Стоимость для иностранцев'] = cost.get('foreigner')
                data['Год цен'] = cost.get('year')

            faculties = api_program.get('faculties', [])
            if faculties:
                data['Факультеты'] = [{'название': f.get('title'), 'ссылка': f.get('link')} for f in faculties]

        # JSON программа
        json_program = json_data.get('jsonProgram', {})
        if json_program:
            about = json_program.get('about', {})
            if about:
                data['Описание (краткое)'] = about.get('lead')
                data['Описание (подробное)'] = about.get('desc')
                data['Видео'] = about.get('video', [])

            career = json_program.get('career', {})
            if career:
                data['Карьера (подробная)'] = career.get('lead')

            data['Социальные сети'] = json_program.get('social', {})
            data['Достижения студентов'] = json_program.get('achievements', [])

            faq = json_program.get('faq', [])
            if faq:
                data['FAQ (подробные)'] = {item.get('question', ''): item.get('answer', '') for item in faq}

            comments = json_program.get('comments', [])
            if comments:
                data['Отзывы выпускников'] = [
                    {'имя': c.get('fullName'), 'год_выпуска': c.get('year'), 'сообщение': c.get('message')}
                    for c in comments
                ]

        # Команда
        team = json_data.get('team', [])
        if team:
            data['Команда программы'] = [
                {
                    'имя': f"{m.get('firstName', '')} {m.get('lastName', '')} {m.get('middleName', '')}".strip(),
                    'степень': m.get('degree'),
                    'должности': m.get('positions', [])
                }
                for m in team
            ]

        data['Даты вступительных экзаменов'] = json_data.get('examDates', [])
        data['Похожие программы'] = json_data.get('similarPrograms', [])

        return data

    def parse_admission_info(self, json_data):
        data = {}
        api_program = json_data.get('apiProgram', {})
        directions = api_program.get('directions', [])

        for direction in directions:
            quotas = direction.get('admission_quotas', {})
            if quotas:
                data['Квоты на поступление'] = {
                    'бюджетные места': quotas.get('budget'),
                    'контрактные места': quotas.get('contract'),
                    'целевое обучение': quotas.get('target_reception'),
                    'особая квота': quotas.get('invalid'),
                    'отдельная квота': quotas.get('special_quota'),
                    'контракт для иностранцев': quotas.get('contract_foreign'),
                }

            disciplines = direction.get('disciplines', [])
            if disciplines:
                data['Способы поступления'] = [
                    {
                        'приоритет': d.get('priority'),
                        'название': d.get('discipline', {}).get('title'),
                        'описание': d.get('discipline', {}).get('description'),
                        'тип_поступления': d.get('discipline', {}).get('admission_type'),
                    }
                    for d in disciplines
                ]

        return data

    def download_pdf(self, url, program_name):
        if not url:
            return None

        try:
            response = self.get_page(url)
            if not response:
                return None

            # Создаем уникальное имя файла для каждой программы
            filename = f"{program_name}_учебный_план.pdf"
            file_path = self.pdf_dir / filename

            with open(file_path, 'wb') as f:
                f.write(response.content)

            self.logger.info(f"PDF скачан: {filename}")
            return file_path

        except Exception as e:
            self.logger.error(f"Ошибка скачивания PDF: {e}")
            return None

    def parse_pdf(self, pdf_path):
        if not pdf_path or not pdf_path.exists():
            return ""

        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    try:
                        text += page.extract_text() + "\n"
                    except:
                        continue
            return text.strip()
        except:
            return ""

    def process_pdfs(self, data, program_name):
        pdf_content = {}

        # Ищем ссылку на учебный план
        pdf_url = data.get('Учебный план (PDF)')
        if pdf_url:
            file_path = self.download_pdf(pdf_url, program_name)
            if file_path:
                content = self.parse_pdf(file_path)
                if content:
                    pdf_content['учебный_план'] = content
                    self.logger.info(f"Обработан PDF для программы: {program_name}")

        return pdf_content

    def parse_program(self, url, program_name):
        self.logger.info(f"Парсинг программы: {program_name}")

        response = self.get_page(url)
        if not response:
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')
        json_data = self.extract_json_data(soup)

        data = {}
        data.update(self.parse_basic_info(soup))

        faq = self.parse_faq(soup)
        if faq:
            data['Вопросы и ответы'] = faq

        data.update(self.parse_enhanced_info(json_data))
        data.update(self.parse_admission_info(json_data))

        # Обрабатываем PDF
        pdf_content = self.process_pdfs(data, program_name)
        if pdf_content:
            data['PDF_документы'] = pdf_content

        data['_metadata'] = {
            'url': url,
            'parsed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'parser_version': '2.1'
        }

        return data

    def save_data(self, data, filename):
        try:
            with open(self.data_dir / filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            self.logger.info(f"Сохранено: {filename}")
            return True
        except Exception as e:
            self.logger.error(f"Ошибка сохранения {filename}: {e}")
            return False

    def run(self):
        self.logger.info("Начало парсинга")

        for program_name, url in self.programs.items():
            try:
                data = self.parse_program(url, program_name)
                if data:
                    filename = f"{program_name}.json"
                    self.save_data(data, filename)

                time.sleep(1)  # Пауза между запросами

            except Exception as e:
                self.logger.error(f"Ошибка обработки {program_name}: {e}")

        self.logger.info("Парсинг завершен")


if __name__ == "__main__":
    parser = ITMOParser()
    parser.run()
