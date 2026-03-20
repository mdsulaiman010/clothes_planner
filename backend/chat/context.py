def build_system_prompt(page_context: dict) -> str:
    base = (
        "You are a helpful fashion assistant for a digital wardrobe app. "
        "You help users organize their clothes, suggest outfits, and provide fashion advice. "
        "Be friendly, concise, and context-aware based on what the user is currently doing in the app."
    )

    page = page_context.get('page', '')
    selected_items = page_context.get('selectedItems', [])
    category = page_context.get('category', '')

    context_parts = [base]

    if page == 'upload':
        context_parts.append(
            "The user is currently on the upload page, adding new clothing items to their wardrobe. "
            "Help them with questions about categorization, what items to add, or wardrobe gaps."
        )
    elif page == 'wardrobe':
        context_parts.append(
            f"The user is browsing their wardrobe{f', currently viewing {category} items' if category else ''}. "
            "Help them find items, suggest outfit combinations, or discuss their collection."
        )
        if selected_items:
            context_parts.append(f"They have selected {len(selected_items)} item(s).")
    elif page == 'tryon':
        context_parts.append(
            "The user is on the virtual try-on page, experimenting with how clothes look on them. "
            "Help with styling tips, fit advice, or combination suggestions."
        )

    return '\n\n'.join(context_parts)
