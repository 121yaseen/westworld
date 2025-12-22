from abc import ABC, abstractmethod
from typing import List, Tuple

class Theme(ABC):
    @property
    @abstractmethod
    def node_names(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def ambiance_tags(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def host_names(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def host_personas(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def visitor_archetypes(self) -> List[Tuple[str, str]]:
        pass
    
    @abstractmethod
    def get_clues(self, artifact_node_name: str, neighbor_names: List[str], other_node_name: str) -> List[str]:
        pass

    @abstractmethod
    def get_red_herrings(self) -> List[str]:
        pass


class WestworldTheme(Theme):
    @property
    def node_names(self) -> List[str]:
        return [
            "Mesa Hub", "Sweetwater Plaza", "Ghost Ridge", "Copper Spur", "Lazarus Gulch",
            "Coyote Pass", "Ironwood", "Mirror Lake", "Dust Town", "Glass Arroyo",
            "Red Mesa", "Nightfall Station",
        ]

    @property
    def ambiance_tags(self) -> List[str]:
        return [
            "dusty", "lantern-lit", "echoing", "quiet", "busy", "stormy", "sunlit",
            "foggy", "windy", "shadowy",
        ]

    @property
    def host_names(self) -> List[str]:
        return [
            "Maeve", "Dolores", "Teddy", "Stubbs", "Armistice", "Clementine",
            "Elsie", "Hector", "Lawrence", "Angela", "Coughlin", "Juliet",
        ]

    @property
    def host_personas(self) -> List[str]:
        return [
            "bartender", "sheriff", "rancher", "card dealer", "drifter", "herbalist",
            "armorer", "railway clerk", "hacker in disguise", "archivist", "prospector",
        ]

    @property
    def visitor_archetypes(self) -> List[Tuple[str, str]]:
        return [
            ("Avery", "Analyst"),
            ("Blake", "Diplomat"),
            ("Cass", "Scout"),
        ]

    def get_clues(self, artifact_node_name: str, neighbor_names: List[str], other_node_name: str) -> List[str]:
         return [
            f"The artifact is hidden in {artifact_node_name}.",
            f"You must go to the place connected to {neighbor_names[0]}.",
            "The lock requires three confirmed rumors to open.",
            f"It is not in {other_node_name}."
        ]

    def get_red_herrings(self) -> List[str]:
        return [
            "The rattlesnakes are restless.",
            "I heard a ghost haunts the old mine.",
            "The train is late today.",
            "These violent delights have violent ends.",
        ]


class HarryPotterTheme(Theme):
    @property
    def node_names(self) -> List[str]:
        return [
            "Great Hall", "Potions Dungeon", "Forbidden Forest", "Ravenclaw Tower", 
            "Hagrid's Hut", "Quidditch Pitch", "Library", "Room of Requirement",
            "Gryffindor Common Room", "Slytherin Common Room", "Astronomy Tower", "Owlery"
        ]

    @property
    def ambiance_tags(self) -> List[str]:
        return [
            "magical", "floating candles", "dark and damp", "mysterious", "cozy", 
            "windy", "filled with whispers", "ancient", "smelling of parchment", "spectral"
        ]

    @property
    def host_names(self) -> List[str]:
        return [
            "Nearly Headless Nick", "The Bloody Baron", "Peeves", "Moaning Myrtle", "The Fat Lady",
            "The Grey Lady", "Professor Binns", "Dobby", "Kreacher", "Filch", "Mrs. Norris"
        ]

    @property
    def host_personas(self) -> List[str]:
        return [
            "ghost", "poltergeist", "portrait", "house-elf", "cranky caretaker", 
            "spectral teacher", "prankster", "guardian"
        ]

    @property
    def visitor_archetypes(self) -> List[Tuple[str, str]]:
        return [
            ("Harry", "The Chosen One"),
            ("Hermione", "The Brightest Witch"),
            ("Ron", "The Loyal Friend"),
        ]

    def get_clues(self, artifact_node_name: str, neighbor_names: List[str], other_node_name: str) -> List[str]:
        return [
            f"The Horcrux is hidden in {artifact_node_name}.",
            f"You must fly to the place connected to {neighbor_names[0]}.",
            "The Dark Lord's protection requires three secrets to break.",
            f"It is technically not in {other_node_name}, if you catch my drift."
        ]

    def get_red_herrings(self) -> List[str]:
        return [
            "Nargles are behind it, I suspect.",
            "Beware of the Whomping Willow.",
            "The stairs like to change on Fridays.",
            "Did you hear? Potter is in the dungeons again.",
        ]
