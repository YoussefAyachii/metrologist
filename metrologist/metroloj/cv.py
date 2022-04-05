#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 26 14:23:09 2022
@author: Youssef Ayachi

This module aims to reproduce the coefficient of variation (CV) report
generated by MetroloJ, an ImageJ plugin.
Given a .tif file, this module will produce the following elements:
    - original images with rois (region of interests) marked on them.
    - microscopy info dataframe
    - rois' histogram ploting the number of pixels per gray intensity value
    for all the images
    - dataframe enclosing info about the roi's pixels with significant
    intensities.

Note: rois are defined as the central 20% of the given image.
Note: Code tested on one or multi image .tif file (from homogeneity and
cv samples)

"""

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from skimage.filters import threshold_otsu
from skimage.segmentation import clear_border
from skimage.morphology import closing, square
from skimage.draw import polygon_perimeter
from skimage.color import label2rgb
from skimage.measure import label, regionprops

import common as cm


# Get roi (default central 20% of the original image) for a given 2d image


def get_roi_default(tiff_final):
    """
    Select the default Region Of Interest (ROI) from the initial image,
    e.i. select the central 20% of the whole np.array and return it.
    The returned arrays, one per image, are enclosed in a list.

    Parameters
    ----------
    tiff_data : np.array
        3d np.array representing the image data.
        the first dimension should represent image index (z,x,y).

    Returns
    -------
    list : list
        list of 2 elements:
            1. dict enclosing info about the ROI
            2. list of ROIs pictures to display
    """

    ROI_info = {}
    ROI_nb_pixels_list = []
    ROI_start_pixel_list = []
    ROI_end_pixel_list = []
    ROI_Original_ratio_list = []

    # we assume that images from same tiff file have the same size
    try:
        nb_images, xdim, ydim = tiff_final.shape
    except ValueError:
        xdim, ydim = tiff_final.shape
        nb_images = 1

    # we want the central 20% of the original image
    h, w = int(xdim*0.4), int(ydim*0.4)
    # roi defined by top-left (start) and bottom-right (end) pixels
    startx, endx = int(xdim//2 - h//2), int(xdim//2 + h//2)
    starty, endy = int(ydim//2 - w//2), int(ydim//2 + w//2)
    roi_start_pixel = [startx, starty]
    roi_end_pixel = [endx, endy]

    # initialization of the desired output
    xdim_roi, ydim_roi = endx-startx, endy-starty
    roi_final = np.zeros((nb_images, xdim_roi, ydim_roi), dtype=int)

    if nb_images == 1:
        roi_data_temp = tiff_final[startx:endx, starty:endy]

        # add roi_temp to the final roi
        roi_final = roi_data_temp

        # lists for info dataframe
        roi_nb_pixels = roi_data_temp.shape
        ROI_nb_pixels_list.append(roi_nb_pixels)
        ROI_start_pixel_list.append(roi_start_pixel)
        ROI_end_pixel_list.append(roi_end_pixel)
        ROI_Original_ratio_list.append("20%")

    else:
        for i in range(nb_images):
            roi_data_temp = tiff_final[i][startx:endx, starty:endy]

            # add roi_temp to the final roi
            roi_final[i] = roi_data_temp

            # lists for info dataframe
            roi_nb_pixels = roi_data_temp.shape
            ROI_nb_pixels_list.append(roi_nb_pixels)
            ROI_start_pixel_list.append(roi_start_pixel)
            ROI_end_pixel_list.append(roi_end_pixel)
            ROI_Original_ratio_list.append("20%")

    # dict enclosing info about the ROI
    ROI_info["ROI_nb_pixels"] = ROI_nb_pixels_list
    ROI_info["ROI_start_pixel"] = ROI_start_pixel_list
    ROI_info["ROI_end_pixel"] = ROI_end_pixel_list
    ROI_info["ROI_Original_ratio"] = ROI_Original_ratio_list
    ROI_info = pd.DataFrame(ROI_info)

    return ROI_info, roi_final


"""
# ex1: one image in tiff file
img = cm.get_images_from_multi_tiff(path_cv)
roi_df, roi_array = get_roi_default(img[0])

# ex1: 2 images in tiff file
img = cm.get_images_from_multi_tiff(path_cv)
roi_df, roi_array = get_roi_default(img)
"""


# 2. Compute cv


def get_segmented_image(img):
    """
    Given a 2D np.array, it replaces all the pixels with an intensity below
    a threshold otsu value by 0 as well as artifacts connected to image border.

    Parameters
    ----------
    img : np.array
        Original image in a 2D format.

    Returns
    -------
    img : np.array
        2D np.array where only pixels with significant intensity are given
        non null values.

    """
    # define threshold
    thresh = threshold_otsu(img)
    # boolean matrice: True represent the pixels of interest
    bw = closing(img > thresh, square(3))
    # remove artifacts connected to image border
    cleared = clear_border(bw)

    # get segmented image
    xtot, ytot = np.shape(img)

    for i in range(xtot):
        for j in range(ytot):
            if not cleared[i, j]:
                img[i, j] = 0
    return img


"""
# ex:
img = cm.get_images_from_multi_tiff(path_cv)[0]
get_segmented_image(img)
"""


def get_cv_table_global(tiff_data, output_dir=None):
    """
    For each np.arrays of the given list, it computes the Coefficient of
    Variation (cv) of the central 20% (ROI).

    Parameters
    ----------
    tiff_data : np.array
        3d np.arrays
    output_dir : str, optional
        if specified, save the table to the output_dir.
        the default is None.

    Returns
    -------
    cv_table : dict
        dict enclosing info about the pixels with significant intensities
        of the segemented ROI of each given np.array:
            1. standard deviation
            2. mean
            3. number of pixels
            4. Coefficient of Variation (cv)
            5. Normalized cv: cv relative to min value.

    """
    std_intensity_list = []
    mean_intensity_list = []
    nb_pixels_list = []
    cv_list = []

    for i in range(len(tiff_data)):
        img_temp = get_segmented_image(tiff_data[i])
        ball_intensity_vec_temp = img_temp[img_temp != 0]
        # Statistics
        std_intensity_temp = np.std(ball_intensity_vec_temp)
        mean_intensity_temp = np.mean(ball_intensity_vec_temp)
        nb_pixels_temp = len(ball_intensity_vec_temp)
        cv_temp = std_intensity_temp/mean_intensity_temp

        std_intensity_list.append(std_intensity_temp)
        mean_intensity_list.append(mean_intensity_temp)
        nb_pixels_list.append(nb_pixels_temp)
        cv_list.append(cv_temp)

    cv_normalized = np.divide(cv_list, min(cv_list))

    cv_dict = {"sd": std_intensity_list,
               "average": mean_intensity_list,
               "nb_pixels": nb_pixels_list,
               "cv": cv_list,
               "cv_relative_to_min": cv_normalized
               }
    if output_dir is not None:
        pd.DataFrame(cv_dict).to_csv(output_dir+"cv.csv")

    return cv_dict


"""
# ex1: one image in tiff file
img = cm.get_images_from_multi_tiff(path_cv)
get_cv_table_global(img)

# ex2: 2 images in tiff file
img = cm.get_images_from_multi_tiff(path_cv)
get_cv_table_global(img)
"""


# 3. Report: Get Tiff images with ROIs marked on them.


def get_marked_roi_and_label_single_img(img, show=False, output_dir=None):
    """
    This function do the following on a single np.array (image):
    - labelise by a diffrent color the pixels that are considered when
    computing the cv value, i.e. having a higher intensity than the
    threshold otsu value.
    - mark by a red rectangle the region of pixels having an intensity higher
    than a threshold otsu
    which are used
    - mark by a white rectangle the roi region, i.e. the central 20% region
    of the inputed image.

    Parameters
    ----------
    img : np.array
        2d np.array
    show : bool, optional
        If True, the resulting array (image) is shown. The default is False.
    output_dir : str, optional.
        directory path to save the image.

    Returns
    -------
    image_label_overlay : np.array
        2d np.array corresponding to the digital image where:
            - pixels that are considered when computing the cv value are marked
            by a different color.
            - the region of pixels having an intensity higher than a threshold
            otsu is mark by a red rectangle.
            - roi region, i.e. the central 20% region of the inputed image,
            marked by a white rectangle.
    """

    image = img.astype(np.uint8)
    thresh = threshold_otsu(image)
    bw = closing(image > thresh, square(3))

    # limit the labelization to the roi region
    # roi coordinates
    roi_info, roi_arrays = get_roi_default(image)
    roi_minr, roi_minc = roi_info["ROI_start_pixel"][0]
    roi_maxr, roi_maxc = roi_info["ROI_end_pixel"][0]

    # remove outside roi region
    cleared = clear_border(bw, buffer_size=int((512/2)-roi_minr))

    # label image regions
    label_image = label(cleared)

    # set background to transparent
    image_label_overlay = label2rgb(label_image, image=image, bg_label=0)

    # mark roi on image_label_overlay
    rr, cc = polygon_perimeter([roi_minr, roi_minr, roi_maxr, roi_maxr],
                               [roi_minc, roi_maxc, roi_maxc, roi_minc],
                               shape=image.shape,
                               clip=True)
    image_label_overlay[rr, cc, :] = 255

    # show locally
    if show is True:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(image_label_overlay)

        ax.set_axis_off()
        plt.tight_layout()

        plt.show()

    # save
    if output_dir is not None:
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(image_label_overlay)

        ax.set_axis_off()
        plt.tight_layout()

        output_path = output_dir + "0.roi.png"
        plt.savefig(output_path,
                    bbox_inches='tight',
                    pad_inches=0,
                    format="png")
    else:
        return image_label_overlay


"""
img = cm.get_images_from_multi_tiff(path_cv)
output_path = "/Users/Youssef/Desktop/"
get_marked_roi_and_label_single_img(img[1],show=True, output_dir=output_path)
get_marked_roi_and_label_single_img(img[0],show=True)
"""

# get_marked_roi_and_label_multi_img


def get_marked_roi_and_label_multi_img(tiff_data, output_dir=None):
    """
    This function show or save the multi tiff file into distinct png files.
    For each image of the input multitif file, this function:
    - labelises by a diffrent color the pixels that are considered when
    computing the cv value, i.e. having a higher intensity than the
    threshold otsu value.
    - marks by a red rectangle the region of pixels having an intensity higher
    than a threshold otsu
    which are used
    - marks by a white rectangle the roi region, i.e. the central 20% region
    of the inputed image.

    Parameters
    ----------
    tiff_data : numpay.ndarray
        3d np.array representing the image data.
    output_dir : str, optional
        Output directory path. The default is None.

    Returns
    -------
    fig_list : list
        1D list of figures of type matplotlib.figure.Figure.
    """

    fig_list = []
    for i in range(len(tiff_data)):
        image_temp = get_marked_roi_and_label_single_img(
            tiff_data[i],
            show=True
            )

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.imshow(image_temp)
        ax.set_axis_off()
        plt.tight_layout()
        fig_list.append(fig)

        if output_dir is not None:
            plt.savefig(output_dir+f"{i}.roi.png",
                        bbox_inches='tight',
                        pad_inches=0,
                        format="png")
    return fig_list



"""
tiff_data = cm.get_images_from_multi_tiff(path_cv)
output_path = "/Users/Youssef/Desktop/"
figures = get_marked_roi_and_label_multi_img(tiff_data, output_path)
figures = get_marked_roi_and_label_multi_img(tiff_data)
get_marked_roi_and_label_multi_img(tiff_data)[0]
"""


# 4. Get histogram : nb of pixels per intensity values


def get_hist_data(img, nb_img=1):
    """
    get from an image the number of pixels per gray intensity.

    Parameters
    ----------
    img : np.array
        Original 2D image.
    nb_img : int
        number of images in a multitiff file.
        the default is 1.

    Returns
    -------
    if nb_img = 1 :
        intensity_value
        nb_pixel
    else :
        table of intensity_value
        table of nb_pixel
    """

    if nb_img==1:
        # convert matrix to one vector
        ball_intensity_vec = get_segmented_image(img)
        ball_intensity_vec.flatten()
        ball_intensity_vec = ball_intensity_vec[ball_intensity_vec != 0]
        np.ndarray.sort(ball_intensity_vec)

        # build a table
        intensity_value, nb_pixel = np.unique(
            ball_intensity_vec,
            return_counts=True)
        return intensity_value, nb_pixel

    else:
        intensity_value_tab = np.zeros(shape=(255,nb_img))
        nb_pixel_tab = np.zeros(shape=(255,nb_img))
        for i in range(nb_img):
            # convert matrix to one vector
            ball_intensity_vec = get_segmented_image(img[i])
            ball_intensity_vec.flatten()
            ball_intensity_vec = ball_intensity_vec[ball_intensity_vec != 0]
            np.ndarray.sort(ball_intensity_vec)

            # build a table
            intensity_value, nb_pixel = np.unique(
                ball_intensity_vec,
                return_counts=True)
            
            # store into a numpy array
            intensity_value_tab[:,i] = intensity_value
            nb_pixel_tab[:,i] = nb_pixel
        return intensity_value_tab, nb_pixel_tab


"""
# ex:
img = cm.get_images_from_multi_tiff(path_cv)
roi_df, roi_arrays = get_roi_default(img)
get_hist_data(roi_arrays[0])
get_hist_data(img, nb_img=2)
"""


def get_hist_nbpixel_vs_grayintensity(tiff_data, output_dir=None):
    """
    For a given list of images in np.array format, return a histogram
    of the number of pixels per gray intensity of each of the given arrays.

    Parameters
    ----------
    tiff_data : list
        List of np.arrays.

    Returns
    -------
    fig : plot
        Histogram of the number of pixels per gray intensity.
    """

    fig = plt.figure()
    colors = ["r", "g", "b", "c", "m", "y", "k", "w"]

    roi_arrays = get_roi_default(tiff_data)[1]
    for i in range(len(roi_arrays)):
        hist_x, hist_y = get_hist_data(roi_arrays[i])
        plt.plot(
            hist_x, hist_y, marker=".", markersize=0.2, color=colors[i],
            label="ROI " + str(i), linewidth=0.8, figure=fig
            )

    plt.title("Intensity histogram", figure=fig)
    plt.xlim((0, 256))
    plt.xlabel("Gray levels")
    plt.ylabel("Nb Pixels")
    plt.legend()
    plt.title("Intensity histogram", figure=fig)

    if output_dir is not None:
        plt.savefig(output_dir+"hist.png",
                    bbox_inches='tight',
                    pad_inches=0,
                    format="png")   

    return fig


"""
# ex:
img = cm.get_images_from_multi_tiff(path_cv)
get_hist_nbpixel_vs_grayintensity(img)
"""

"""
Generate cv report Given 1 .tif file enclosing one or more 2D images.
"""


def cv_report(
        tiff_data,
        microscope_type, wavelength, NA, sampling_rate, pinhole,
        output_dir=None
        ):
    """
    Generate the different componenent of the cv report and stock them in
    a list.
    If output_dir specified, it saves the different elements of the 
    cv report in the specified directory.

    Parameters
    ----------
    tiff_data : list
        list of images in a 2D np.arrays format.
    microscope_type : str

    wavelength : float
        In nm.
    NA : int or float
        Numerical aperture.
    sampling_rate : str
        In number of pixels. Ex: "1.0x1.0x1.0".
    pinhole : int or float
        In airy units.
    output_dir : str, optional
        if specified, all elements will be saved in the mentioned dir:
        1.Save as .png: original images with ROIs marked on them.
        2.Save as .csv: microscopy info dataframe.
        3.Save as .png: histogram of the number of pixels per gray 
        intensity value for all the images.
        4.Save as .csv: Dataframe enclosing info about the pixels with
        significant intensities of the segemented ROI of each
        given np.array.

    Returns
    -------
    cv_report_elements : list
        List of all the cv report elements:
            1. original images with ROIs marked on them.
            2. microscopy info dataframe
            3. histogram of the number of pixels per gray intensity value
            for all the images
            4. Dataframe enclosing info about the pixels with significant
            intensities of the segemented ROI of each given np.array.
    """

    # Get Histogram : Nbpixel VS Gray scale
    hist_nbpixels_vs_grayscale = get_hist_nbpixel_vs_grayintensity(
        tiff_data,
        output_dir=output_dir
        )

    # Get Images with Marked ROIs on them
    img_original_marked_roi_label = get_marked_roi_and_label_multi_img(
        tiff_data,
        output_dir=output_dir
        )

    # Get Microscope info dataframe
    microscopy_info_table = cm.get_microscopy_info(
        microscope_type, wavelength, NA, sampling_rate, pinhole
        )
    if output_dir is not None:
        microscopy_info_table.to_csv(output_dir+"microscopy_info")

    # Get cv table
    cv_table = get_cv_table_global(
        tiff_data,
        output_dir=output_dir
        )

    # return all elements
    cv_report_elements = [img_original_marked_roi_label,
                          microscopy_info_table,
                          hist_nbpixels_vs_grayscale,
                          cv_table]

    return cv_report_elements


"""
# ex1:
img = cm.get_images_from_multi_tiff(path_cv)
cvreport_elements_1 = get_cv_report_elements(
    img, None, "Confocal", 460, 1.4, "1.0x1.0x1.0", 1
    )
cvreport_elements_1[0]
cvreport_elements_1[0][0]
cvreport_elements_1[0][1]
cvreport_elements_1[1]
cvreport_elements_1[2]
cvreport_elements_1[3]

# ex2: save
output_path_cv = "/Users/Youssef/Documents/IBDML/"+\
    "MetroloJ-for-python/outputs/cv_outputs/"
cvreport_elements_2 = get_cv_report_elements(
    img, output_path_cv, "Confocal", 460, 1.4, "1.0x1.0x1.0", 1
    )
"""
