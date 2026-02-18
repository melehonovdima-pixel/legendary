# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
Скрипт для тестирования API УК ЖКХ
Запустите после запуска основного приложения
"""

import requests
import json
from typing import Optional

BASE_URL = "http://127.0.0.1:5500"

class APITester:
    def __init__(self):
        self.token: Optional[str] = None
        self.user_id: Optional[int] = None
    
    def print_header(self, text: str):
        """Печать заголовка"""
        print(f"\n{'='*60}")
        print(f"  {text}")
        print(f"{'='*60}\n")
    
    def print_result(self, response: requests.Response):
        """Печать результата запроса"""
        print(f"Status: {response.status_code}")
        try:
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except:
            print(f"Response: {response.text}")
        print()
    
    def test_register(self):
        """Тест регистрации"""
        self.print_header("1. Тестирование регистрации нового пользователя")
        
        data = {
            "username": "79161234567",
            "password": "testpass123",
            "fullname": "Тестовый Пользователь Иванович",
            "address": "ул. Тестовая, д. 1, кв. 1"
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/register", json=data)
        self.print_result(response)
        
        if response.status_code == 201:
            self.user_id = response.json()["id"]
            print("✓ Регистрация успешна!")
        else:
            print("✗ Ошибка регистрации")
    
    def test_login(self, username: str = "admin", password: str = "admin123"):
        """Тест входа в систему"""
        self.print_header("2. Тестирование входа в систему")
        
        data = {
            "username": username,
            "password": password
        }
        
        response = requests.post(f"{BASE_URL}/api/auth/login", json=data)
        self.print_result(response)
        
        if response.status_code == 200:
            self.token = response.json()["access_token"]
            print(f"✓ Вход выполнен успешно!")
            print(f"Token: {self.token[:50]}...")
        else:
            print("✗ Ошибка входа")
    
    def test_get_current_user(self):
        """Тест получения информации о текущем пользователе"""
        self.print_header("3. Получение информации о текущем пользователе")
        
        if not self.token:
            print("✗ Нет токена. Сначала выполните вход.")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/api/auth/me", headers=headers)
        self.print_result(response)
        
        if response.status_code == 200:
            print("✓ Данные пользователя получены")
    
    def test_create_request(self):
        """Тест создания заявки"""
        self.print_header("4. Создание новой заявки")
        
        if not self.token:
            print("✗ Нет токена. Сначала выполните вход.")
            return
        
        data = {
            "type": "plumbing",
            "description": "Протекает кран на кухне. Требуется срочная замена прокладки. Вода капает постоянно."
        }
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{BASE_URL}/api/requests", json=data, headers=headers)
        self.print_result(response)
        
        if response.status_code == 201:
            request_id = response.json()["id"]
            print(f"✓ Заявка создана! ID: {request_id}")
            return request_id
        else:
            print("✗ Ошибка создания заявки")
            return None
    
    def test_get_requests(self):
        """Тест получения списка заявок"""
        self.print_header("5. Получение списка заявок")
        
        if not self.token:
            print("✗ Нет токена. Сначала выполните вход.")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/api/requests", headers=headers)
        self.print_result(response)
        
        if response.status_code == 200:
            print(f"✓ Получено заявок: {len(response.json())}")
    
    def test_get_users(self):
        """Тест получения списка пользователей (только для админа)"""
        self.print_header("6. Получение списка пользователей (только админ)")
        
        if not self.token:
            print("✗ Нет токена. Сначала выполните вход.")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/api/users", headers=headers)
        self.print_result(response)
        
        if response.status_code == 200:
            print(f"✓ Получено пользователей: {len(response.json())}")
        elif response.status_code == 403:
            print("✗ Нет прав доступа (требуется роль менеджера или администратора)")
    
    def test_dashboard_stats(self):
        """Тест получения статистики"""
        self.print_header("7. Получение статистики дашборда (только менеджер/админ)")
        
        if not self.token:
            print("✗ Нет токена. Сначала выполните вход.")
            return
        
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(f"{BASE_URL}/api/stats/dashboard", headers=headers)
        self.print_result(response)
        
        if response.status_code == 200:
            print("✓ Статистика получена")
        elif response.status_code == 403:
            print("✗ Нет прав доступа (требуется роль менеджера или администратора)")
    
    def run_all_tests(self):
        """Запуск всех тестов"""
        print("\n" + "="*60)
        print("  ТЕСТИРОВАНИЕ API УК ЖКХ")
        print("="*60)
        print(f"  Base URL: {BASE_URL}")
        print("="*60)
        
        try:
            # Проверка доступности API
            response = requests.get(f"{BASE_URL}/docs")
            if response.status_code not in [200, 404]:
                print("\n✗ API недоступен! Убедитесь, что сервер запущен.")
                return
            
            # Тесты
            # self.test_register()  # Раскомментируйте для теста регистрации
            self.test_login()
            self.test_get_current_user()
            self.test_create_request()
            self.test_get_requests()
            self.test_get_users()
            self.test_dashboard_stats()
            
            self.print_header("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
            print("✓ Все тесты выполнены!")
            
        except requests.exceptions.ConnectionError:
            print("\n✗ Не удалось подключиться к API!")
            print("  Убедитесь, что сервер запущен: python main.py")
        except Exception as e:
            print(f"\n✗ Ошибка при тестировании: {e}")


if __name__ == "__main__":
    tester = APITester()
    tester.run_all_tests()
