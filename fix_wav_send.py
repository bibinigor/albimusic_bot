with open('/root/albimusic-bot/run_monitor_notify.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Заменяем отправку файла на отправку ссылки
old = '''                    file_id = str(uuid.uuid4())[:8]
                    wav_path = f'{temp_dir}/track_{file_id}.wav'

                    async with aiohttp.ClientSession() as session:
                        async with session.get(file_url) as response:
                            if response.status == 200:
                                with open(wav_path, 'wb') as f:
                                    f.write(await response.read())
                                logger.info(f"✅ WAV файл скачан: {wav_path}")

                                # Отправляем как документ
                                from aiogram.types import InputFile
                                wav_file = InputFile(wav_path, filename="music.wav")
                                await bot.send_document(
                                    chat_id=user_id,
                                    document=wav_file,
                                    caption="🎵 WAV файл готов!"
                                )
                                logger.info(f"✅ WAV файл отправлен user {user_id}")

                                # Удаляем временный файл
                                os.remove(wav_path)
                                logger.info(f"🗑️ Временный WAV удален: {wav_path}")
                            else:
                                logger.error(f"❌ Ошибка скачивания WAV: HTTP {response.status}")
                                await bot.send_message(user_id, "❌ Не удалось загрузить WAV файл. Попробуйте позже.")
                                await bot.close()
                                return False  # Ошибка - пометить как ERROR_NOTIFIED'''

new = '''                    # WAV файлы обычно >50MB (лимит Telegram), отправляем ссылку
                    await bot.send_message(
                        chat_id=user_id,
                        text=f"🎵 *WAV файл готов!*\\n\\n📥 Скачать: {file_url}\\n\\n⚠️ Файл доступен 24 часа",
                        parse_mode="Markdown"
                    )
                    logger.info(f"✅ WAV ссылка отправлена user {user_id}")'''

content = content.replace(old, new)

with open('/root/albimusic-bot/run_monitor_notify.py', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ WAV теперь отправляется как ссылка")
