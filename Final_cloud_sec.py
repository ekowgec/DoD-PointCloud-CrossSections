"""
program for # This program performs the following tasks:
# 1. Imports necessary libraries including os, numpy, cloudComPy, open3d, and time.
# 2. Defines functions to:
#    - Load data from LAS files, including initializing cloudComPy, loading point cloud data,
#      getting global shift coordinates, loading segmentation boundary polyline, and loading cross-sectional polyline.
#    - Generate ortho sections based on a cross-sectional polyline, step, width, and vertical direction.
#    - Extract ortho and cloud sections from a point cloud based on provided parameters.
#    - Save ortho and cloud sections to files in LAS and text formats.
#    - Visualize cross-sections using Open3D.
#    - Measure the processing time of the main function.
# 3. Implements the main function which:
#    - Specifies the directory containing LAS files.
#    - Loads data from LAS files using the load_data function.
#    - Prompts the user for input regarding ortho section parameters.
#    - Generates ortho sections, extracts sections, creates output directories,
#      saves sections, and visualizes cross-sections for each LAS file.
#    - Prints the total processing time upon completion.
# 4. Runs the main function if the script is executed as the main program.


@author:Charles Ghartey
"""
# Import necessary libraries
import os
import numpy as np
import cloudComPy as cc  
import open3d as o3d
import time  

# Function to load data
def load_data(directory):
    # Initialize cloudComPy
    cc.initCC() 
    # Get list of files in the specified directory
    files = os.listdir(directory)
    # Filter LAS files
    las_files = [file for file in files if file.endswith(".las")]
    # Initialize empty lists to store data
    clouds, polys, cross_polylines = [], [], []
    # Iterate over LAS files
    for las_file in las_files:
        # Load point cloud data
        cloud = cc.loadPointCloud(os.path.join(directory, las_file))
        print(f"Cloud name: {cloud.getName()} for file {las_file}")
        # Get global shift coordinates
        x, y, z = cc.ccShiftedObject.getGlobalShift(cloud)
        print(f"Coordinates of shift: ({x}, {y}, {z})")
        # Load segmentation boundary polyline
        poly = cc.loadPolyline(os.path.join(directory, "polyline.dxf"),
                               mode=cc.CC_SHIFT_MODE.XYZ, x=x, y=y, z=z)
        print(f"Segmentation boundary: {poly.getName()} for file {las_file}")
        poly.setClosed(True)
        polys.append(poly)
        # Load cross-sectional polyline
        cross_polyline = cc.loadPolyline(os.path.join(directory, "north1.dxf"),
                                         mode=cc.CC_SHIFT_MODE.XYZ, x=x, y=y, z=z)
        cross_polyline.setClosed(False)
        cross_polylines.append(cross_polyline)
        clouds.append(cloud)

    return clouds, polys, cross_polylines

# Function to generate ortho sections
def generate_ortho_sections(cross_polyline, step, width, vertical_direction):
    # Generate ortho sections based on given parameters
    orthoPolys = cross_polyline.generateOrthoSections(step, width, vertical_direction)
    return orthoPolys

# Function to extract sections from the point cloud
def extract_sections(cloud, cross_polyline, orthoPolys, default_section_thickness):
    # Extract ortho and cloud sections from the point cloud
    orthoSections = cc.extractPointsAlongSections([cloud], orthoPolys,
                                                  defaultSectionThickness=default_section_thickness,
                                                  extractSectionsAsClouds=True,
                                                  extractSectionsAsEnvelopes=False)
    cloudSections = cc.extractPointsAlongSections([cloud], [cross_polyline],
                                                  defaultSectionThickness=default_section_thickness,
                                                  extractSectionsAsClouds=True,
                                                  extractSectionsAsEnvelopes=False)
    return orthoSections, cloudSections

# Function to save sections to files
def save_sections(orthoSections, orthoOutputDir, cloudSections, cloudOutputDir, file_name):
    # Save ortho sections
    for i, section in enumerate(orthoSections):
        file_path = os.path.join(orthoOutputDir, f"{file_name}_ortho_section_{i}.laz")
        cc.SavePointCloud(section, file_path)
        
    # Save cloud sections
    for i, section in enumerate(cloudSections):
        file_path = os.path.join(cloudOutputDir, f"{file_name}_cloud_section_{i}.laz")
        xyz_path = os.path.join(cloudOutputDir, f"{file_name}_cloud_section_{i}.txt")
        cc.SavePointCloud(section, file_path)
        # Save point cloud data to a text file
        cc.SavePointCloud(section, xyz_path)
       
# Function to visualize cross-sections
def visualize_cross_sections(cloudSections, default_section_thickness):
    for i, section in enumerate(cloudSections):
        # Convert ccPointCloud to NumPy array
        points = cc.ccPointCloud.toNpArray(section)
        
        # Create Open3D point cloud object
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        # Get the number of points in the point cloud
        num_points = len(points)
        
        # Print the description of the section
        print(f"Visualizing cross-section {i+1} with {num_points} points.")
        
        # Visualize the point cloud using Open3D
        o3d.visualization.draw_geometries([pcd], 
                                           window_name=f"Cross-section slice {i+1} with slice thickness {default_section_thickness}m ",
                                           width=700, height=700)

# Main function
def main():
    # Start measuring processing time
    start_time = time.time()
    
    # Specify the directory containing LAS files
    directory = r"D:\CE_666\Final"
    
    # Load data
    clouds, polys, cross_polylines = load_data(directory)
    
    for cloud, poly, cross_polyline in zip(clouds, polys, cross_polylines):
        # User input for ortho section parameters
        step = float(input("Enter the step for ortho sections: "))
        width = float(input("Enter the width for ortho sections: "))
        vertical_direction = int(input("Enter the vertical direction for ortho sections (O (oX), 1, (oY), 2 (oZ)): "))
        default_section_thickness = float(input("Enter the default section thickness: "))
        
        # Generate ortho sections
        orthoPolys = generate_ortho_sections(cross_polyline, step, width, vertical_direction)
       
        # Extract sections
        orthoSections, cloudSections = extract_sections(cloud, cross_polyline, orthoPolys, default_section_thickness)
       
        # Create output directories
        orthoOutputDir = os.path.join(directory, "ortho_sections")
        cloudOutputDir = os.path.join(directory, "cloud_sections")
        os.makedirs(orthoOutputDir, exist_ok=True)
        os.makedirs(cloudOutputDir, exist_ok=True)
        
        # Get the base name of the LAS file
        file_name = os.path.splitext(os.path.basename(cloud.getName()))[0]
       
        # Save sections
        save_sections(orthoSections, orthoOutputDir, cloudSections, cloudOutputDir, file_name)
       
        # Visualize cross-sections
        visualize_cross_sections(cloudSections, default_section_thickness)
    
    # End measuring processing time
    end_time = time.time()
    total_time = end_time - start_time
    print("\n")
    print(f"Total processing time: {total_time} seconds")

if __name__ == "__main__":
    main()
