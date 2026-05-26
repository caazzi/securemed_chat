import reflex as rx

config = rx.Config(
    app_name="preconsult",
    show_reflex_badge=False,
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)