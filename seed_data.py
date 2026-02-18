# -*- coding: utf-8 -*-
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

"""
Скрипт для заполнения базы данных тестовыми данными
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from database import SessionLocal, init_db
from models import User, Request, Comment, SystemSettings, UserRole, UserStatus, RequestStatus, RequestType
from auth import get_password_hash


def create_test_data():
    """Создать тестовые данные в базе"""
    
    # Инициализация БД
    init_db()
    
    db: Session = SessionLocal()
    
    try:
        print("Начинаю создание тестовых данных...")
        
        # Проверка существующих данных
        existing_users = db.query(User).count()
        if existing_users > 1:  # > 1 потому что админ создается автоматически
            print(f" В базе уже есть {existing_users} пользователей.")
            response = input("Продолжить и добавить новые данные? (y/n): ")
            if response.lower() != 'y':
                print("Отменено.")
                return
        
        # 1. Создание пользователей
        print("\n1. Создание пользователей...")
        
        users_data = [
            {
                "username": "79161111111",
                "password": "client123",
                "fullname": "Иванов Петр Сергеевич",
                "address": "ул. Ленина, д. 10, кв. 12",
                "role": UserRole.CLIENT,
                "status": UserStatus.CONFIRMED
            },
            {
                "username": "79162222222",
                "password": "client123",
                "fullname": "Сидорова Мария Ивановна",
                "address": "ул. Ленина, д. 10, кв. 25",
                "role": UserRole.CLIENT,
                "status": UserStatus.CONFIRMED
            },
            {
                "username": "79163333333",
                "password": "client123",
                "fullname": "Козлов Дмитрий Александрович",
                "address": "ул. Ленина, д. 10, кв. 38",
                "role": UserRole.CLIENT,
                "status": UserStatus.CONFIRMED
            },
            {
                "username": "79164444444",
                "password": "executor123",
                "fullname": "Петров Алексей Викторович",
                "address": None,
                "role": UserRole.EXECUTOR,
                "status": UserStatus.CONFIRMED
            },
            {
                "username": "79165555555",
                "password": "executor123",
                "fullname": "Смирнов Игорь Сергеевич",
                "address": None,
                "role": UserRole.EXECUTOR,
                "status": UserStatus.CONFIRMED
            },
            {
                "username": "79166666666",
                "password": "executor123",
                "fullname": "Васильев Николай Петрович",
                "address": None,
                "role": UserRole.EXECUTOR,
                "status": UserStatus.CONFIRMED
            },
            {
                "username": "79167777777",
                "password": "manager123",
                "fullname": "Морозов Андрей Владимирович",
                "address": "Офис УК",
                "role": UserRole.MANAGER,
                "status": UserStatus.CONFIRMED
            },
            {
                "username": "79168888888",
                "password": "client123",
                "fullname": "Новиков Сергей Иванович",
                "address": "ул. Ленина, д. 10, кв. 55",
                "role": UserRole.CLIENT,
                "status": UserStatus.PENDING
            },
        ]
        
        users = []
        for user_data in users_data:
            # Проверяем, не существует ли уже пользователь
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                user = User(
                    username=user_data["username"],
                    hashed_password=get_password_hash(user_data["password"]),
                    fullname=user_data["fullname"],
                    address=user_data["address"],
                    role=user_data["role"],
                    status=user_data["status"],
                    is_active=True
                )
                db.add(user)
                users.append(user)
                print(f"   Создан пользователь: {user_data['fullname']} ({user_data['role'].value})")
            else:
                users.append(existing)
                print(f"  - Пользователь уже существует: {user_data['fullname']}")
        
        db.commit()
        print(f" Создано пользователей: {len([u for u in users if u.id is None]) or 'обновлены существующие'}")
        
        # Получаем пользователей из БД для создания заявок
        clients = db.query(User).filter(User.role == UserRole.CLIENT).all()
        executors = db.query(User).filter(User.role == UserRole.EXECUTOR).all()
        
        # 2. Создание заявок
        print("\n2. Создание заявок...")
        
        requests_data = [
            {
                "client": clients[0],
                "executor": executors[0],
                "type": RequestType.PLUMBING,
                "description": "Протекает кран на кухне. Требуется замена прокладки.",
                "status": RequestStatus.COMPLETED,
                "priority": 1,
                "days_ago": 7
            },
            {
                "client": clients[0],
                "executor": executors[1],
                "type": RequestType.ELECTRICITY,
                "description": "Не работает розетка в коридоре. Требуется проверка проводки.",
                "status": RequestStatus.IN_PROGRESS,
                "priority": 2,
                "days_ago": 2
            },
            {
                "client": clients[1],
                "executor": executors[0],
                "type": RequestType.PLUMBING,
                "description": "Засор в раковине в ванной комнате. Вода не уходит.",
                "status": RequestStatus.IN_PROGRESS,
                "priority": 2,
                "days_ago": 1
            },
            {
                "client": clients[1],
                "executor": None,
                "type": RequestType.ELEVATOR,
                "description": "Лифт застревает между этажами. Требуется срочный ремонт.",
                "status": RequestStatus.NEW,
                "priority": 3,
                "days_ago": 0
            },
            {
                "client": clients[2],
                "executor": None,
                "type": RequestType.CLEANING,
                "description": "Требуется уборка подъезда после ремонта.",
                "status": RequestStatus.NEW,
                "priority": 1,
                "days_ago": 1
            },
            {
                "client": clients[2],
                "executor": executors[2],
                "type": RequestType.HEATING,
                "description": "Батареи в квартире холодные. Требуется проверка отопительной системы.",
                "status": RequestStatus.ASSIGNED,
                "priority": 3,
                "days_ago": 0
            },
        ]
        
        requests = []
        for req_data in requests_data:
            created_at = datetime.utcnow() - timedelta(days=req_data["days_ago"])
            deadline = created_at + timedelta(hours=24)
            
            request = Request(
                client_id=req_data["client"].id,
                executor_id=req_data["executor"].id if req_data["executor"] else None,
                type=req_data["type"],
                description=req_data["description"],
                status=req_data["status"],
                priority=req_data["priority"],
                created_at=created_at,
                deadline=deadline
            )
            
            if req_data["status"] == RequestStatus.ASSIGNED:
                request.assigned_at = created_at + timedelta(hours=2)
            
            if req_data["status"] == RequestStatus.IN_PROGRESS:
                request.assigned_at = created_at + timedelta(hours=2)
                request.started_at = created_at + timedelta(hours=3)
            
            if req_data["status"] == RequestStatus.COMPLETED:
                request.assigned_at = created_at + timedelta(hours=1)
                request.started_at = created_at + timedelta(hours=2)
                request.completed_at = created_at + timedelta(hours=4)
            
            db.add(request)
            requests.append(request)
            print(f"   Создана заявка: {req_data['type'].value} ({req_data['status'].value})")
        
        db.commit()
        print(f" Создано заявок: {len(requests)}")
        
        # 3. Создание комментариев
        print("\n3. Создание комментариев...")
        
        comments_data = [
            {
                "request": requests[0],
                "user": executors[0],
                "text": "Принял заявку в работу. Приеду сегодня после обеда.",
                "hours_ago": 168
            },
            {
                "request": requests[0],
                "user": executors[0],
                "text": "Работа выполнена. Заменил прокладку в кране.",
                "hours_ago": 164
            },
            {
                "request": requests[0],
                "user": clients[0],
                "text": "Спасибо! Все работает отлично.",
                "hours_ago": 163
            },
            {
                "request": requests[1],
                "user": executors[1],
                "text": "Начинаю работу. Проверяю проводку.",
                "hours_ago": 24
            },
            {
                "request": requests[2],
                "user": executors[0],
                "text": "Засор устранен, сейчас проверяю работу системы.",
                "hours_ago": 12
            },
        ]
        
        for comment_data in comments_data:
            created_at = datetime.utcnow() - timedelta(hours=comment_data["hours_ago"])
            
            comment = Comment(
                request_id=comment_data["request"].id,
                user_id=comment_data["user"].id,
                text=comment_data["text"],
                created_at=created_at
            )
            db.add(comment)
            print(f"   Создан комментарий к заявке #{comment_data['request'].id}")
        
        db.commit()
        print(f" Создано комментариев: {len(comments_data)}")
        
        # 4. Проверка системных настроек
        print("\n4. Проверка системных настроек...")
        setting = db.query(SystemSettings).filter(
            SystemSettings.key == "response_time_hours"
        ).first()
        
        if setting:
            print(f"   Настройка response_time_hours уже существует: {setting.value} часов")
        else:
            setting = SystemSettings(
                key="response_time_hours",
                value="24",
                description="Время ответа на заявку (часы)"
            )
            db.add(setting)
            db.commit()
            print(f"   Создана настройка response_time_hours: 24 часа")
        
        print("\n" + "="*60)
        print("   ТЕСТОВЫЕ ДАННЫЕ УСПЕШНО СОЗДАНЫ!")
        print("="*60)
        
        # Вывод сводной информации
        print("\n Статистика:")
        print(f"  Пользователей: {db.query(User).count()}")
        print(f"    - Клиентов: {db.query(User).filter(User.role == UserRole.CLIENT).count()}")
        print(f"    - Исполнителей: {db.query(User).filter(User.role == UserRole.EXECUTOR).count()}")
        print(f"    - Менеджеров: {db.query(User).filter(User.role == UserRole.MANAGER).count()}")
        print(f"    - Администраторов: {db.query(User).filter(User.role == UserRole.ADMIN).count()}")
        print(f"  Заявок: {db.query(Request).count()}")
        print(f"    - Новых: {db.query(Request).filter(Request.status == RequestStatus.NEW).count()}")
        print(f"    - В работе: {db.query(Request).filter(Request.status == RequestStatus.IN_PROGRESS).count()}")
        print(f"    - Выполненных: {db.query(Request).filter(Request.status == RequestStatus.COMPLETED).count()}")
        print(f"  Комментариев: {db.query(Comment).count()}")
        
        print("\n Учетные данные для тестирования:")
        print("\nАдминистратор:")
        print("  Username: admin")
        print("  Password: admin123")
        print("\nМенеджер:")
        print("  Username: 79167777777")
        print("  Password: manager123")
        print("\nИсполнитель:")
        print("  Username: 79164444444")
        print("  Password: executor123")
        print("\nКлиент:")
        print("  Username: 79161111111")
        print("  Password: client123")
        
    except Exception as e:
        print(f"\n✗ Ошибка при создании тестовых данных: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_test_data()
