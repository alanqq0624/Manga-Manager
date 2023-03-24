import logging

from src.Common import ResourceLoader
from src.Layouts import layout_factory
from src.MetadataManager.GUI.OneTimeMessageBox import OneTimeMessageBox
from src.MetadataManager.GUI.widgets.MessageBoxWidget import MessageBoxButton
from src.Settings import Settings, SettingHeading

logger = logging.getLogger()

icon_path = ResourceLoader.get('icon.ico')

def execute_gui():
    # Ensure there are some settings, if not, set them as the default
    Settings().set_default(SettingHeading.ExternalSources, 'default_metadata_source', "AniList")
    Settings().set_default(SettingHeading.ExternalSources, 'default_cover_source', "MangaDex")
    Settings().set_default(SettingHeading.Main, 'selected_layout', "default")

    layout_name = Settings().get(SettingHeading.Main, 'selected_layout')
    logger.info(f"Initializing '{layout_name}' layout")
    app = layout_factory.get(layout_name)()

    try:
        app.iconbitmap(icon_path)
    except:
        logger.exception("Exception loading icon")

    OneTimeMessageBox("test_welcome_to_mm").\
        with_title("Welcome to MangaManager").\
        with_actions([MessageBoxButton(0, "Thanks")]).\
        build().prompt()

    app.mainloop()


