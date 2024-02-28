import logging
from enum import StrEnum

import requests

from MangaManager.Common import get_invalid_person_tag
from ComicInfo import ComicInfo
from MangaManager.Common.errors import MangaNotFoundError
from MangaManager.DynamicLibController.models.IMetadataSource import IMetadataSource
from MangaManager.Settings.SettingControl import SettingControl, SettingControlType
from MangaManager.Settings.SettingSection import SettingSection
from MangaManager.Settings.Settings import Settings


class MangaUpdatesPerson(StrEnum):
    Author = "author",
    Artist = "artist",


class MangaUpdates(IMetadataSource):
    name = "MangaUpdates"
    _log = logging.getLogger()
    person_mapper = {
        "Author": [
            "Writer"
        ],
        "Artist": [
            "Penciller",
            "Inker",
            "CoverArtist"
        ]
    }

    def init_settings(self):
        self.settings = [
            SettingSection(self.name, self.name, [
                SettingControl(MangaUpdatesPerson.Author, "Author", SettingControlType.Text, "Writer",
                               "How metadata field will map to ComicInfo fields", self.is_valid_person_tag, self.trim),
                SettingControl(MangaUpdatesPerson.Artist, "Artist", SettingControlType.Text,
                               "Penciller, Inker, CoverArtist", "How metadata field will map to ComicInfo fields",
                               self.is_valid_person_tag, self.trim),
            ])
        ]

    def save_settings(self):
        # Update person_mapper when this is called as it indicates the settings for the provider might have changed
        self.person_mapper[MangaUpdatesPerson.Author] = Settings().get(self.name, MangaUpdatesPerson.Author).split(',')
        self.person_mapper[MangaUpdatesPerson.Artist] = Settings().get(self.name, MangaUpdatesPerson.Artist).split(',')

    @staticmethod
    def is_valid_person_tag(key, value):
        invalid_people = get_invalid_person_tag(value)

        if len(invalid_people) == 0:
            return ""
        return ", ".join(invalid_people) + " are not a valid tags"

    @classmethod
    def get_cinfo(cls, comic_info_from_ui) -> ComicInfo | None:
        # We need to take what's already in the UI and allow fetching to merge the data in
        comicinfo = ComicInfo()
        
        data = cls._get_series_details(comic_info_from_ui.series, {})

        # Basic Info
        comicinfo.series = data["title"].strip()
        comicinfo.summary = IMetadataSource.clean_description(data.get("description"), remove_source=True)
        comicinfo.genre = ", ".join([i["genre"] for i in data["genres"]]).strip()
        comicinfo.tags = ", ".join([i["category"] for i in data["categories"]])
        comicinfo.web = data["url"].strip()
        comicinfo.manga = "Yes" if data["type"] == "Manga" else "No"
        comicinfo.year = data["year"]

        # People Info
        cls.update_people_from_mapping(data["authors"], cls.person_mapper, comicinfo,
                                   lambda item: item["name"],
                                   lambda item: item["type"])

        comicinfo.publisher = (", ".join([ i["publisher_name"] for i in data["publishers"] ]))

        # Extended
        comicinfo.community_rating = round(data["bayesian_rating"]/2, 1)

        return comicinfo

    @classmethod
    def _get_series_id(cls, search_params, logging_info):
        try:
            response = requests.post('https://api.mangaupdates.com/v1/series/search', json=search_params)
        except Exception as e:
            cls._log.exception(e, extra=logging_info)
            cls._log.warning('Manga Manager is unfamiliar with this error. Please log an issue for investigation.',
                             extra=logging_info)
            return None

        cls._log.debug(f'Search Params: {search_params}')
        # cls._log.debug(f'Response JSON: {response.json()}')

        if len(response.json()['results']) == 0:
            raise MangaNotFoundError("MangaUpdates",search_params['search'])
        try:
            return response.json()['results'][0]['record']['series_id']
        except TypeError:
            return None

    @classmethod
    def _get_series_details(cls, manga_title, logging_info):
        search_params = {
            "search": manga_title,
            "page": 1,
            "per_page": 1
        }

        try:
            series_details = requests.get('https://api.mangaupdates.com/v1/series/' + str(cls._get_series_id(search_params, {})))
        except Exception as e:
            cls._log.exception(e, extra=logging_info)
            cls._log.warning('Manga Manager is unfamiliar with this error. Please log an issue for investigation.',
                             extra=logging_info)
            return None
            
        return series_details.json()
