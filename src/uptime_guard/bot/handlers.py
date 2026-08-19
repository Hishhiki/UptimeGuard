import uuid
from urllib.parse import urlparse

from sqlalchemy import select
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, Message
from telegram.ext import ContextTypes

from uptime_guard.database import session_factory, redis_client
from uptime_guard.models.target import Target
from uptime_guard.models.user import User


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("➕ Добавить сайт", callback_data="menu_add")],
        [InlineKeyboardButton("📋 Мои сайты", callback_data="menu_list")],
        [InlineKeyboardButton("📊 Статистика", callback_data="menu_stats")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message:
        return

    tg_id = update.effective_user.id
    username = update.effective_user.username or f"user_{tg_id}"

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalars().first()

        if not user:
            user = User(telegram_id=tg_id, username=username)
            session.add(user)
            await session.commit()

    await update.message.reply_text(
        f"Привет, {username}! 👋\n\n"
        "Я UptimeGuard — бот для мониторинга сайтов.\n"
        "Выбери действие в меню ниже:",
        reply_markup=get_main_menu_keyboard(),
    )


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_user or not update.message or not update.message.text:
        return

    tg_id = update.effective_user.id
    text = update.message.text.strip()

    parsed_url = urlparse(text)
    if not parsed_url.scheme or not parsed_url.netloc:
        await update.message.reply_text(
            "Неверный формат URL. Пожалуйста, убедитесь, что ссылка содержит http:// или https://"
        )
        return

    async with session_factory() as session:
        result = await session.execute(select(User).where(User.telegram_id == tg_id))
        user = result.scalars().first()

        if not user:
            await update.message.reply_text("Сначала напишите /start для регистрации.")
            return

        target = Target(user_id=user.id, url=text)
        session.add(target)
        await session.commit()

    await update.message.reply_text(
        f"Сайт {text} успешно добавлен в мониторинг!",
        reply_markup=get_main_menu_keyboard(),
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    if not query or not update.effective_user or not isinstance(query.message, Message):
        return

    await query.answer()
    tg_id = update.effective_user.id
    data = query.data

    if data is None:
        return

    if data == "menu_add":
        await query.message.reply_text("Просто пришлите мне ссылку на сайт (начиная с http:// или https://) в этот чат 👇")

    elif data == "menu_list":
        async with session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == tg_id))
            user = result.scalars().first()
            if not user:
                await query.message.reply_text("Сначала напишите /start")
                return

            targets_result = await session.execute(select(Target).where(Target.user_id == user.id))
            targets_list = targets_result.scalars().all()

            if not targets_list:
                await query.message.reply_text("У вас пока нет добавленных сайтов.", reply_markup=get_main_menu_keyboard())
                return

            for index, target in enumerate(targets_list, start=1):
                status = "✅ Активен" if target.is_active else "⏸ На паузе"
                text = f"{index}. {target.url}\nСтатус: {status}"
                
                toggle_btn_text = "▶️ Возобновить" if not target.is_active else "⏸ Пауза"
                keyboard = [
                    [
                        InlineKeyboardButton(toggle_btn_text, callback_data=f"toggle_{target.id}"),
                        InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{target.id}")
                    ]
                ]
                await query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
            
            # В конце снова показываем меню
            await query.message.reply_text("Главное меню:", reply_markup=get_main_menu_keyboard())

    elif data == "menu_stats":
        async with session_factory() as session:
            result = await session.execute(select(User).where(User.telegram_id == tg_id))
            user = result.scalars().first()
            if not user:
                await query.message.reply_text("Сначала напишите /start")
                return

            targets_result = await session.execute(select(Target).where(Target.user_id == user.id))
            targets_list = targets_result.scalars().all()

            if not targets_list:
                await query.message.reply_text("У вас пока нет добавленных сайтов.", reply_markup=get_main_menu_keyboard())
                return

            lines = ["📊 *Ваша статистика:*\n"]
            for target in targets_list:
                total_str = await redis_client.get(f"stats:total:{target.id}")
                success_str = await redis_client.get(f"stats:success:{target.id}")
                last_ping_str = await redis_client.get(f"stats:last_ping:{target.id}")

                total = int(total_str) if total_str else 0
                success = int(success_str) if success_str else 0
                last_ping = int(last_ping_str) if last_ping_str else 0

                uptime_pct = (success / total * 100) if total > 0 else 0
                
                status_emoji = "🟢" if target.is_active else "⏸"
                
                lines.append(f"{status_emoji} *{target.url}*")
                if total == 0:
                    lines.append("   _Нет данных (ожидание проверки)_")
                else:
                    lines.append(f"   Аптайм: {uptime_pct:.2f}%")
                    lines.append(f"   Пинг: {last_ping} ms")
                lines.append("")
                
            await query.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

    elif data.startswith("toggle_"):
        try:
            target_id_str = data.split("_")[1]
            target_uuid = uuid.UUID(target_id_str)
        except ValueError:
            return

        async with session_factory() as session:
            res = await session.execute(select(Target).where(Target.id == target_uuid))
            target = res.scalars().first()
            if target:
                target.is_active = not target.is_active
                await session.commit()
                status = "✅ Активен" if target.is_active else "⏸ На паузе"
                
                toggle_btn_text = "▶️ Возобновить" if not target.is_active else "⏸ Пауза"
                keyboard = [
                    [
                        InlineKeyboardButton(toggle_btn_text, callback_data=f"toggle_{target.id}"),
                        InlineKeyboardButton("❌ Удалить", callback_data=f"delete_{target.id}")
                    ]
                ]
                text = f"Сайт: {target.url}\nСтатус: {status}"
                await query.edit_message_text(text=text, reply_markup=InlineKeyboardMarkup(keyboard))

    elif data.startswith("delete_"):
        try:
            target_id_str = data.split("_")[1]
            target_uuid = uuid.UUID(target_id_str)
        except ValueError:
            return

        async with session_factory() as session:
            res = await session.execute(select(Target).where(Target.id == target_uuid))
            target = res.scalars().first()
            if target:
                url = target.url
                await session.delete(target)
                await session.commit()
                await query.edit_message_text(text=f"❌ Сайт {url} удален из мониторинга.")

