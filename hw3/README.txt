Homework Assignment 3
Andrea Goldstein -- angoldst@gmail.com

git repo -- https://github.com/angoldst/Homework/tree/master/hw3

Folder contents:
Hw3_pt1.ipynb 	-- Recreate own figure
Hw3_pt2.ipynb 	-- Recreate stock figure
Hw3_pt3.ipynb 	-- Data brush assignment
Fig_2_Goldstein_JNeuro_2013 -- clipping of figure to recreate for pt1
hw_3_Data/ 	-- folder contains .csv and text files for running scripts
	figA.csv 		-- data for left portion of pt1
	figB.csv 		-- data for right portion of pt1
	flowers.csv 		-- data for pt3
	google_data.txt 	-- data for pt2
	ny_temps.txt 		-- data for pt2
	yahoo_data.txt 		-- data for pt2
	stocks.png 		-- comparison image for pt2

File specifics:

Hw3_pt1.ipynb -- should run through python notebook data path set to generic hw_3_Data/folder. prints newly generated figure recreation in the notebook inline

Hw3_pt2.ipynb -- should run through python notebook data path set to generic hw_3_Data/ prints newly generated stock graph in the notebook inline

Hw3_pt3.ipynb -- Should have full basic functionality drawing subplots, generating rectangles and changing opacity of those points not contained in rectangle. If you're interested in getting the specific data points enclosed by the rectangle you can access it through brushObj.origData(brushObj.mask)

The top part of the code contains all the definitions and functions necessary to run the actual code in the below pane. User can specifically edit:
fname -- filename of the data to load
cat -- specify which data column should be used for categorization (column must be string array)
nonCat -- user can choose to look at all of the columns that were not specified specifically as the category info or enter in specific column headers of interest. If this   list is longer than 5 entries it will send an error and will not run. Will also send an error if there is missing data or if the input is not float/int. 




