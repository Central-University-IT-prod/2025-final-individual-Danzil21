from aiogram.types import InlineKeyboardButton


def page_factory(offset, max_offset, callback_data_factory, **extra_args):
    current_page = InlineKeyboardButton(
        text=str(offset + 1), callback_data='none_state'
    )

    def make_cb(offset):
        return callback_data_factory(offset=offset, **extra_args).pack()


    if max_offset == 1:
        if offset == 0:
            next_btn = InlineKeyboardButton(
                text='▶️ ' + str(offset + 2),
                callback_data=make_cb(offset=offset + 1)
            )
            return [current_page, next_btn]
        else:
            back_btn = InlineKeyboardButton(
                text=str(offset) + '◀️',
                callback_data=make_cb(offset=offset - 1)
            )
            return [back_btn, current_page]

    else:
        if offset == 0:
            next_btn = InlineKeyboardButton(
                text='▶️ ' + str(offset + 2),
                callback_data=make_cb(offset=offset + 1)
            )
            extra_btn = InlineKeyboardButton(
                text='⏩ ' + str(max_offset + 1),
                callback_data=make_cb(offset=max_offset)
            )
            return [current_page, next_btn, extra_btn]

        elif offset == max_offset:
            back_btn = InlineKeyboardButton(
                text=str(offset) + ' ◀️',
                callback_data=make_cb(offset=offset - 1)
            )
            extra_btn = InlineKeyboardButton(
                text=str(1) + ' ⏪',
                callback_data=make_cb(offset=0)
            )
            return [extra_btn, back_btn, current_page]

        else:
            back_btn = InlineKeyboardButton(
                text=str(offset) + ' ◀️',
                callback_data=make_cb(offset=offset - 1)
            )
            next_btn = InlineKeyboardButton(
                text='▶️ ' + str(offset + 2),
                callback_data=make_cb(offset=offset + 1)
            )
            first_page = InlineKeyboardButton(
                text=str(1) + ' ⏪',
                callback_data=make_cb(offset=0)
            )
            last_page = InlineKeyboardButton(
                text='⏩ ' + str(max_offset + 1),
                callback_data=make_cb(offset=max_offset)
            )
            print(offset, max_offset)
            if offset == 1 and offset + 1 != max_offset:
                return [back_btn, current_page, next_btn, last_page]
            elif offset == 1 and offset + 1 == max_offset:
                return [back_btn, current_page, next_btn]
            elif offset + 1 == max_offset:
                return [first_page, back_btn, current_page, next_btn]
            else:
                return [first_page, back_btn, current_page, next_btn, last_page]
