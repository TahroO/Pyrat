import pygame
from os import walk


# cycle through the folder and add all data to a list
def import_folder(path):
    # list -> []
    surface_list = []

    # list contains of 3 key elements, go through all of them
    for folder_name, sub_folders, img_files in walk(path):
        # first attribute
        for image_name in img_files:
            # construct a destination path for the image
            full_path = path + '/' + image_name
            # use the path to store the image as surface
            image_surface = pygame.image.load(full_path)
            # add image surface to surface list
            surface_list.append(image_surface)

    return surface_list


def import_folder_dict(path):
    # dictionary -> {}
    surface_dict = {}

    # list contains of 3 key elements, go through all of them
    for folder_name, sub_folders, img_files in walk(path):
        # first attribute
        for image_name in img_files:
            # construct a destination path for the image
            full_path = path + '/' + image_name
            # use the path to store the image as surface
            image_surface = pygame.image.load(full_path)
            # separate filename from ending
            surface_dict[image_name.split('.')[0]] = image_surface

    return surface_dict
