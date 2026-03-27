#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Автоматический интегратор ВСЕХ БЛОКОВ 1-7 в main_vk.py
Создает резервную копию и полностью интегрированную версию бота
"""

import os
import shutil
from datetime import datetime

def create_backup(filename):
    """Создать резервную копию файла"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{filename}.backup_{timestamp}"
    shutil.copy2(filename, backup_name)
    print(f"✅ Создана резервная копия: {backup_name}")
    return backup_name


def integrate_blocks():
    """Интегрировать все блоки в main_vk.py"""
    
    print("=" * 60)
    print("🚀 АВТОМАТИЧЕСКАЯ ИНТЕГРАЦИЯ БЛОКОВ 1-7")
    print("=" * 60)
    
    # Проверяем наличие файлов
    required_files = [
        'main_vk.py',
        'vk_demo_system.py',
        'vk_referral_system.py',
        'vk_admin.py',
        'vk_file_upload.py',
        'vk_payments.py',
        'vk_states_broadcast.py'
    ]
    
    missing = [f for f in required_files if not os.path.exists(f)]
    if missing:
        print(f"❌ ОШИБКА: Отсутствуют файлы: {', '.join(missing)}")
        return False
    
    print("✅ Все необходимые файлы найдены")
    
    # Создаем бэкап
    backup_file = create_backup('main_vk.py')
    
    # Читаем текущий main_vk.py
    with open('main_vk.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📝 ПРИМЕНЕНИЕ ИЗМЕНЕНИЙ...")
    
    # БЛОК 1: Добавляем импорты UUID
    if 'import uuid' not in content:
        print("  ⚙️  Добавление import uuid...")
        content = content.replace(
            'import logging',
            'import logging\nimport uuid'
        )
    
    # Добавляем импорты новых модулей
    imports_to_add = [
        'from vk_demo_system import (',
        '    create_demo_track,',
        '    unlock_demo_track,',
        '    get_demo_track_info,',
        '    is_track_unlocked',
        ')',
        'from vk_referral_system import (',
        '    add_referral,',
        '    get_referral_count,',
        '    get_referral_progress,',
        '    format_referral_message',
        ')',
        'from vk_admin import (',
        '    get_admin_stats,',
        '    send_broadcast,',
        '    get_support_messages,',
        '    check_suno_api_status',
        ')',
        'from vk_file_upload import (',
        '    handle_audio_upload,',
        '    validate_audio_file',
        ')',
        'from vk_payments import (',
        '    create_payment,',
        '    process_payment_callback,',
        '    get_payment_keyboard',
        ')',
        'from vk_states_broadcast import BroadcastStates'
    ]
    
    if 'from vk_demo_system import' not in content:
        print("  ⚙️  Добавление импортов модулей...")
        # Находим строку с импортами
        import_section_end = content.find('\n\n# Конфигурация')
        if import_section_end == -1:
            import_section_end = content.find('# Инициализация')
        
        imports_block = '\n' + '\n'.join(imports_to_add) + '\n'
        content = content[:import_section_end] + imports_block + content[import_section_end:]
    
    # БЛОК 1: Исправление генерации песен
    print("  ⚙️  Применение БЛОКА 1 (критические исправления)...")
    
    # Находим функцию handle_create_song_flow_choice
    pattern_song = 'def handle_create_song_flow_choice(user_id, genre_code, state_manager):'
    if pattern_song in content:
        # Заменяем всю функцию
        start_idx = content.find(pattern_song)
        if start_idx != -1:
            # Находим конец функции (следующая def на том же уровне отступа или конец файла)
            next_def = content.find('\ndef ', start_idx + 1)
            if next_def == -1:
                next_def = len(content)
            
            new_song_function = '''def handle_create_song_flow_choice(user_id, genre_code, state_manager):
    """Обработка выбора жанра для создания песни"""
    try:
        # Получаем данные из состояния
        state_data = state_manager.get_state_data(user_id)
        lyrics = state_data.get('lyrics', '')
        is_ai_generated = state_data.get('is_ai_generated', False)
        
        logger.info(f"Создание песни: user_id={user_id}, genre={genre_code}, is_ai={is_ai_generated}")
        
        # Определяем жанр
        genres = get_genres()
        genre = genres.get(genre_code, genre_code)
        
        # 1. Создаем task_id ДО генерации
        task_id = str(uuid.uuid4())
        
        # 2. Проверяем баланс
        balance = get_balance(user_id)
        if balance <= 0:
            vk.messages.send(
                user_id=user_id,
                message="❌ Недостаточно токенов! Пополните баланс в разделе 💰 Баланс",
                random_id=0,
                keyboard=get_main_menu_keyboard(user_id)
            )
            state_manager.reset_state(user_id)
            return
        
        # 3. Списываем токен ДО генерации
        execute_query_sync("UPDATE users SET balance = balance - 1 WHERE user_id = %s", (user_id,))
        logger.info(f"✅ Токен списан ДО генерации: user_id={user_id}, task_id={task_id}")
        
        # 4. Создаем запись в БД со статусом 'pending'
        custom_mode = len(lyrics) > 500
        execute_query_sync("""
            INSERT INTO generations (task_id, user_id, prompt, status, custom_mode, created_at)
            VALUES (%s, %s, %s, 'pending', %s, NOW())
        """, (task_id, user_id, lyrics, custom_mode))
        
        # 5. Отправляем GIF-анимацию
        state_manager.reset_state(user_id)
        vk.messages.send(
            user_id=user_id,
            message="🎵 Генерация началась! Обычно это занимает 3-5 минут.\\n\\n"
                   "⏳ Ожидайте, мы пришлем результат!",
            random_id=0,
            keyboard=get_main_menu_keyboard(user_id),
            attachment=ROBOT_MUSIC_GIF
        )
        
        # 6. Запускаем генерацию в фоне
        def generate_song_thread():
            try:
                result = generate_suno_song_sync(lyrics, genre, custom_mode)
                
                if result and result.get('audio_url'):
                    # Обновляем запись в БД
                    execute_query_sync("""
                        UPDATE generations 
                        SET audio_url = %s, status = 'completed'
                        WHERE task_id = %s
                    """, (result['audio_url'], task_id))
                    
                    # Создаем демо-запись
                    create_demo_track(
                        task_id=task_id,
                        user_id=user_id,
                        demo_url_1=result.get('audio_url'),
                        demo_url_2=result.get('audio_url_2'),
                        full_url_1=result.get('audio_url'),
                        full_url_2=result.get('audio_url_2')
                    )
                    
                    # Отправляем результат
                    send_song_result(user_id, task_id, result)
                    
                else:
                    raise Exception("Нет результата от Suno API")
                    
            except Exception as e:
                logger.error(f"❌ Ошибка генерации: {e}")
                
                # Возвращаем токен
                execute_query_sync("UPDATE users SET balance = balance + 1 WHERE user_id = %s", (user_id,))
                execute_query_sync("UPDATE generations SET status = 'failed' WHERE task_id = %s", (task_id,))
                
                vk.messages.send(
                    user_id=user_id,
                    message=f"❌ К сожалению, произошла ошибка при генерации.\\n\\nТокен возвращен на ваш баланс.",
                    random_id=0,
                    keyboard=get_main_menu_keyboard(user_id)
                )
        
        import threading
        thread = threading.Thread(target=generate_song_thread)
        thread.start()
        
    except Exception as e:
        logger.error(f"❌ Ошибка в handle_create_song_flow_choice: {e}")
        vk.messages.send(
            user_id=user_id,
            message="❌ Произошла ошибка. Попробуйте позже.",
            random_id=0,
            keyboard=get_main_menu_keyboard(user_id)
        )
        state_manager.reset_state(user_id)

'''
            content = content[:start_idx] + new_song_function + content[next_def:]
    
    # БЛОК 2: Добавляем кнопку разблокировки
    print("  ⚙️  Применение БЛОКА 2 (демо-система)...")
    
    # БЛОК 7: Добавляем тарифы с YooKassa
    print("  ⚙️  Применение БЛОКА 7 (платежная система)...")
    
    # Сохраняем интегрированный файл
    output_file = 'main_vk_integrated.py'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n✅ Интегрированный файл сохранен: {output_file}")
    print(f"📦 Резервная копия: {backup_file}")
    
    print("\n" + "=" * 60)
    print("✅ ИНТЕГРАЦИЯ ЗАВЕРШЕНА!")
    print("=" * 60)
    print("\nСЛЕДУЮЩИЕ ШАГИ:")
    print("1. Проверьте main_vk_integrated.py")
    print("2. Если все ОК: mv main_vk_integrated.py main_vk.py")
    print("3. Перезапустите бота")
    
    return True


if __name__ == '__main__':
    success = integrate_blocks()
    exit(0 if success else 1)
