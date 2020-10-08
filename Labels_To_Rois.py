from javax.swing import JFrame, JPanel, JLabel, JButton, JTextField, JFileChooser, JMenuBar, JMenu, JMenuItem, JProgressBar, BoxLayout, Box
from javax.swing import JOptionPane
from javax.swing import JRadioButton,ButtonGroup
from javax.swing import BoxLayout, Box
from java.awt import FlowLayout
from ij import IJ
from ij.plugin.frame import RoiManager
from ij.plugin import RoiEnlarger
from ij.process import ImageProcessor
from ij.measure import ResultsTable, Measurements
from ij.plugin.filter import ParticleAnalyzer
from datetime import time, tzinfo
from ij.gui import Wand
from javax.swing import SwingWorker, SwingUtilities
from java.util.concurrent import ExecutionException
from java.awt import Toolkit as awtToolkit
from tempfile import NamedTemporaryFile
from ij.measure import ResultsTable
from ij.macro import Variable
from os import listdir
from os.path import isfile, join
import time
import datetime
import math
import os
import re



###########################################################
####################  Before we begin #####################
###########################################################

gvars = {} # Create dictionary to store variables created within functions
gvars['eroded_pixels'] = 0 # initialize

myTempFile = NamedTemporaryFile(suffix='.zip')
gvars['tempFile'] = myTempFile.name

#Set the original directory of the filechooser to the home folder
fc = JFileChooser()
gvars['original_JFileChooser'] = fc.getCurrentDirectory()
gvars['path_JFileChooser'] = gvars['original_JFileChooser']

###########################################################
####################  Define SwingWorker ##################
###########################################################

class LabelToRoi_Task(SwingWorker):

    def __init__(self, imp):
        SwingWorker.__init__(self)
        self.imp = imp

    def doInBackground(self):
        imp = self.imp
        print "started"

        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print st

        # Disable frame3 buttons in GUI while loading ROIs
        f2_btn_original.setEnabled( 0 )
        f2_btn_label.setEnabled( 0 )
        f2_btn_prev.setEnabled( 0 )
        f2_btn_next.setEnabled( 0 )


        RM = RoiManager()        # we create an instance of the RoiManager class
        rm = RM.getRoiManager()  # "activate" the RoiManager otherwise it can behave strangely
        rm.reset()
        rm.runCommand(imp,"Show All without labels") # we make sure we see the ROIs as they are loading


        imp2 = imp.duplicate()
        ip = imp2.getProcessor()
        width = imp2.getWidth()
        height = imp2.getHeight() - 1

        max_label = int(imp2.getStatistics().max)
        max_digits = int(math.ceil(math.log(max_label,10))) # Calculate the number of digits for the name of the ROI (padding with zeros)
        IJ.setForegroundColor(0, 0, 0) # We pick black color to delete the label already computed

        for j in range(height):
           for i in range(width):
              current_pixel_value = ip.getValue(i,j)
              if current_pixel_value > 0:
                 IJ.doWand(imp2, i, j, 0.0, "Legacy smooth");

                 # We add this ROI to the ROI manager
                 roi = imp2.getRoi()
                 roi.setName(str(int(current_pixel_value)).zfill(max_digits))
                 rm.addRoi(roi)

                 ip.fill(roi) # Much faster than IJ.run(imp2, "Fill", ....

                 # Update ProgressBar
                 progress = int((current_pixel_value / max_label) * 100)
                 self.super__setProgress(progress)

        rm.runCommand(imp,"Sort") # Sort the ROIs in the ROI manager
        rm.runCommand(imp,"Show All without labels")

        ts = time.time()
        st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')
        print st

        print "Finished"


    def done(self):
        try:
            self.get()  #raise exception if abnormal completion
            awtToolkit.getDefaultToolkit().beep()

            RM = RoiManager()
            rm = RM.getRoiManager()
            self.super__setProgress(100) #
            rm.runCommand(self.imp,"Show All without labels")

            ### We save a temporary RoiSet
            temp_roi_path = gvars['tempFile']
            rm.runCommand("Save", temp_roi_path)
            print "Temp ROIs Saved"

            # We change visibility from frame2 to frame3 once the labelToRoi finishes loading rois
            frame3.setVisible(True)
            frame2.setVisible(False)

            # Enable frame3 buttons in GUI after loading
            f2_btn_original.setEnabled( 1 )
            f2_btn_label.setEnabled( 1 )
            f2_btn_prev.setEnabled( 1 )
            f2_btn_next.setEnabled( 1 )

        except ExecutionException, e:
            raise SystemExit, e.getCause()

################################################################################################
########################### Label to ROI Multiple ##############################################
################################################################################################
class LabelToRoi_Multiple_Task(SwingWorker):

    def __init__(self, files, pix_erosion_mult,label_update):
        #self.gui = gui
        SwingWorker.__init__(self)
        self.files = files
        self.pix_erosion_mult = pix_erosion_mult
        self.label_update = label_update

        self.task_finished = False # Flag to know the state of the task


    def doInBackground(self):
       try:                # In case there is an error, so that FIJI doesn't crash
          print "INICIO"
          print self.files
          print self.pix_erosion_mult

          label_files = [f for f in self.files if f.endswith('_label.png') or
                                                  f.endswith('_label.tif') or
                                                  f.endswith('_label.jpg')]
          total_label_files = len(label_files)

          print "total label files:"
          print total_label_files
          gvars["total label files"] = total_label_files


          path_multiple = gvars['path_multiple_image_directory']




          for filenum, f in enumerate(label_files): # Loop through the files in the directory
            self.label_update(filenum+1, total_label_files)
            label_file = f
            print "----"
            print label_file
            original_name = re.sub(r"_label.*", "",f) # get name of the original image without extension

            if (original_name+".tif") in self.files: # for an original image with extension .tif
               original_file = original_name+".tif"
               print original_file
            elif (original_name+".tiff") in self.files: # for an original image with extension .tiff (with double f)
               original_file = original_name+".tiff"
               print original_file
            else:                   # If there is no original image
               original_file = "None"
               print original_file


            print path_multiple

            ########### Section Label To Roi ###########
            RM = RoiManager()
            rm = RM.getRoiManager()
            #label_image = IJ.openImage(path_multiple + "\\" + label_file)
            label_image = IJ.openImage(os.path.join(path_multiple,label_file))

            rm.reset()
            rm.runCommand(label_image,"Show All without labels") # we make sure we see the ROIs as they are loading

            imp2 = label_image.duplicate()
            ip = imp2.getProcessor()
            width = imp2.getWidth()
            height = imp2.getHeight() - 1

            max_label = int(imp2.getStatistics().max)
            max_digits = int(math.ceil(math.log(max_label,10))) # Calculate the number of digits for the name of the ROI (padding with zeros)
            IJ.setForegroundColor(0, 0, 0) # We pick black color to delete the label already computed

            for j in range(height):
               for i in range(width):
                  current_pixel_value = ip.getValue(i,j)
                  if current_pixel_value > 0:
                     IJ.doWand(imp2, i, j, 0.0, "Legacy smooth");

                     # We add this ROI to the ROI manager
                     roi = imp2.getRoi()
                     roi.setName(str(int(current_pixel_value)).zfill(max_digits))
                     rm.addRoi(roi)

                     ip.fill(roi) # Much faster than IJ.run(imp2, "Fill", ....

                     # Update ProgressBar
                     progress = int((current_pixel_value / max_label) * 100)
                     self.super__setProgress(progress)

            rm.runCommand(label_image,"Sort") # Sort the ROIs in the ROI manager
            rm.runCommand(label_image,"Show All without labels")

            ######### Section ROI erotion #########

            for i in range(0, rm.getCount()):
               roi = rm.getRoi(i)
               new_roi = RoiEnlarger.enlarge(roi, -self.pix_erosion_mult) # Important to use this instead of the IJ.run("Enlarge... much faster!!
               rm.setRoi(new_roi,i)

            ####### Section Save ROIs ##############
            print original_name
            #path_to_multiple_ROIs = str(gvars['path_multiple_image_directory']) + "\\" + original_name + "_Erosion_" +str(self.pix_erosion_mult)+ "px_" + "RoiSet.zip"
            path_to_multiple_ROIs = os.path.join(str(gvars['path_multiple_image_directory']), original_name+"_Erosion_"+str(self.pix_erosion_mult)+"px_"+"RoiSet.zip")
            print path_to_multiple_ROIs
            rm.runCommand("Save", path_to_multiple_ROIs)
            print("ROIs saved")

            ####### Section open Original Image ##############
            if original_file != "None": # If there is an original image file besides the label image, we'll measure and generate table of measurements
                print "There is an original image associated to this label"
                original_image = IJ.openImage(os.path.join(path_multiple,original_file))
                IJ.run(original_image, "Enhance Contrast", "saturated=0.35")
                rm.runCommand(original_image,"Show All without labels")
                #original_image.show()

                table_message = []
                is_scaled = original_image.getCalibration().scaled()
                if is_scaled:
                    spatial_cal = "True"
                else:
                    spatial_cal = "False"

                nChannels = original_image.getNChannels()

                print "Total channels:"
                print nChannels
                for current_channel in range(1,nChannels+1):
                   print "Current channel:"
                   print current_channel

                   original_image.setSlice(current_channel)
                   current_slice = str(original_image.getCurrentSlice()) #Get current slice for saving into filename
                   print "Current slice:"
                   print current_slice

                   IJ.run("Clear Results", "")
                   rm.runCommand(original_image,"Select All");
                   rm.runCommand(original_image,"Measure")

                   table = ResultsTable.getResultsTable().clone()
                   IJ.selectWindow("Results")
                   IJ.run("Close")


                   for i in range(0, table.size()):
                      table.setValue('File', i, str(original_name))
                      table.setValue('Channel', i, current_channel)
                      table.setValue('Pixels_eroded', i, str(self.pix_erosion_mult))
                      table.setValue('Spatial_calibration', i, spatial_cal)

                   table.show("Table") # This line is necessary

                   path_to_multiple_Tables = os.path.join(str(gvars['path_multiple_image_directory']), original_name + "_Erosion_" +str(self.pix_erosion_mult)+ "px_Channel_" + str(current_channel) + ".csv")

                   table.save(path_to_multiple_Tables)

                   full_table_path = os.path.join(path_multiple, 'Full_results_table_Erosion_' + str(self.pix_erosion_mult) + 'px.csv')

                   try:
                       if filenum == 0 and current_channel ==1:
                           full_table_file = open(full_table_path, 'w')
                           current_table =  open(path_to_multiple_Tables, 'r')
                           first_line = next(current_table)
                           full_table_file.writelines(first_line)
                           full_table_file.close()
                           current_table.close()

                       with open(full_table_path, 'a') as full_table_file, open(path_to_multiple_Tables, 'r') as current_table:
                           _ = next(current_table) # To avoid appending the header again and again in every iteration
                           for line in current_table:
                              full_table_file.writelines(line)

                   except IOError:
                       JOptionPane.showMessageDialog(None, "Error: The file Full_results_table.csv is open.\nPlease close it and try again!")
                       return #Stop running


                   # Section Save jpg with outlines
                   path_to_multiple_outline = os.path.join(str(gvars['path_multiple_image_directory']),original_name + "_Erosion_" +str(self.pix_erosion_mult)+ "px_" + "Outlines.jpg")
                   outlines_image = original_image.flatten()
                   IJ.saveAs(outlines_image, "JPG", path_to_multiple_outline)

                   IJ.run("Close")






            else:
                print "There is NOT an original image associated to this label"


            label_image.close()

         ####### Section ending ##############

       except Exception as e:
          print e

       self.task_finished = True

    def done(self):
        try:
            self.get()  #raise exception if abnormal completion
            awtToolkit.getDefaultToolkit().beep()

            if self.task_finished:
               if gvars["total label files"] > 0:
                  JOptionPane.showMessageDialog(None, "Processing complete. Files saved to:\n%s" % gvars['path_multiple_image_directory'])
               else:
                  JOptionPane.showMessageDialog(None, "No label images were found")
        except ExecutionException, e:
            raise SystemExit, e.getCause()



###########################################################################

# Definition of function RoiEroder
def RoiEroder(pixels):
   RM = RoiManager()        # we create an instance of the RoiManager class
   rm = RM.getRoiManager()  # "activate" the RoiManager otherwise it can behave strangely

   rm.reset()

   # Re-open temporary original ROIs
   temp_roi_path = gvars['tempFile']
   rm.runCommand("Open", temp_roi_path)
   print "Temp ROIs OPENED"

   for i in range(0, rm.getCount()):
      roi = rm.getRoi(i)
      new_roi = RoiEnlarger.enlarge(roi, -pixels) # Key to use this instead of the IJ.run("Enlarge... much faster!!
      rm.setRoi(new_roi,i)

   gvars['eroded_pixels'] = pixels # Store globally the amount of pixels used to later save them in the ROI file name


###########################################################
####################  Window #1 ###########################
###########################################################

frame1 = JFrame("LabelToRoi: Single or Multiple")
frame1.setLocation(100,100)
frame1.setSize(450,200)
frame1.setLayout(None)

def clic_single(event):
   frame1.setVisible(False)
   frame2.setVisible(True)

def clic_multiple(event):
   print("Click Multiple")
   frame1.setVisible(False)
   frame4.setVisible(True)

# Single Image Button
btn_single = JButton("Single Image", actionPerformed = clic_single)
btn_single.setBounds(120,20,200,50)

# Multiple Image Button
btn_multiple = JButton("Multiple Images", actionPerformed = clic_multiple)
btn_multiple.setBounds(120,90,200,50)


frame1.add(btn_single)
frame1.add(btn_multiple)

frame1.setVisible(True)

###########################################################
####################  Window #2 ###########################
###########################################################



frame2 = JFrame("LabelToRoi - Single Image: Choose paths")
frame2.setLocation(100,100)
frame2.setSize(450,200)
frame2.setLayout(None)


def f2_clic_browse1(event):
   print("Click browse 1")
   fc = JFileChooser()
   fc.setCurrentDirectory(gvars['path_JFileChooser'])
   fc.setDialogTitle('Open original image')
   result = fc.showOpenDialog( None )
   if result == JFileChooser.APPROVE_OPTION :
      message = 'Path to original image %s' % fc.getSelectedFile()
      gvars['path_original_image'] = str(fc.getSelectedFile())
      f2_txt1.setText(gvars['path_original_image'])
      gvars['path_JFileChooser'] = fc.getCurrentDirectory()




   else :
      message = 'Request canceled by user'
   print( message )


def f2_clic_browse2(event):
   print("Click browse 2")
   fc = JFileChooser()
   fc.setCurrentDirectory(gvars['path_JFileChooser'])

   fc.setDialogTitle('Open label image')
   result = fc.showOpenDialog( None )
   if result == JFileChooser.APPROVE_OPTION :
      message = 'Path to label image %s' % fc.getSelectedFile()
      gvars['path_label_image'] = str(fc.getSelectedFile())
      f2_txt2.setText(str(gvars['path_label_image']))
      gvars['path_JFileChooser'] = fc.getCurrentDirectory()
   else :
      message = 'Request canceled by user'

   print( message )


def f2_clic_prev(event):
# I reset the previously browsed images in case of going back to the main frame
   if 'path_original_image' in gvars:
      f2_txt1.setText("")
      del gvars['path_original_image']

   if 'path_label_image' in gvars:
      f2_txt2.setText("")
      del gvars['path_label_image']

   frame1.setVisible(True)
   frame2.setVisible(False)


def f2_clic_next(event):
   if 'path_label_image' not in gvars:
      JOptionPane.showMessageDialog(None, "You have to choose at least a label image")

   elif 'path_original_image' in gvars:
      imp = IJ.openImage(gvars['path_original_image']) # IF there isn't an original image, we'll work only and display the results on the label image

   else:
      gvars['path_original_image'] = gvars['path_label_image']
      imp = IJ.openImage(gvars['path_label_image']) # If there is not an original image and only working with the lable, then show the results of the label

   if 'path_original_image' in gvars and 'path_label_image' in gvars:
      RM = RoiManager()        # we create an instance of the RoiManager class
      rm = RM.getRoiManager()

      gvars["workingImage"] = imp
      imp.show()
      IJ.run(imp, "Enhance Contrast", "saturated=0.35");

      imp2 = IJ.openImage(gvars['path_label_image'])
      task = LabelToRoi_Task(imp2) # Executes the LabelToRoi function defined on top of this script. It is wrapped into a SwingWorker in order for the windows not to freeze
      task.addPropertyChangeListener(update_progress) # To update the progress bar
      task.execute()

      rm.runCommand(imp,"Show All without labels")

      f3_txt1.setText("0")



def update_progress(event):
   # Invoked when task's progress property changes.
   if event.propertyName == "progress":
        progressBar.value = event.newValue




# Browse original image
lbl1 = JLabel("Path to original image")
lbl1.setBounds(40,20,200,20)
f2_btn_original = JButton("Browse", actionPerformed = f2_clic_browse1)
f2_btn_original.setBounds(170,20,100,20)
f2_txt1 = JTextField(10)
f2_txt1.setBounds(280, 20, 120,20)


# Browse label image
lbl2 = JLabel("Path to label image")
lbl2.setBounds(40,50,200,20)
f2_btn_label = JButton("Browse", actionPerformed = f2_clic_browse2)
f2_btn_label.setBounds(170,50,100,20)
f2_txt2 = JTextField(10)
f2_txt2.setBounds(280, 50, 120,20)

# Button Previous
f2_btn_prev = JButton("Previous", actionPerformed = f2_clic_prev)
f2_btn_prev.setBounds(40,120,100,20)

# Button Next
f2_btn_next = JButton("Next", actionPerformed = f2_clic_next)
f2_btn_next.setBounds(300,120,100,20)

# Progress Bar
progressBar = JProgressBar(0, 100, value=0, stringPainted=True)
progressBar.setBounds(40,85,360,20)

frame2.add(lbl1)
frame2.add(f2_btn_original)
frame2.add(f2_txt1)

frame2.add(lbl2)
frame2.add(f2_btn_label)
frame2.add(f2_txt2)

frame2.add(f2_btn_prev)
frame2.add(f2_btn_next)

frame2.add(progressBar)

frame2.setVisible(False)

###########################################################
####################  Window #3 ###########################
###########################################################

frame3 = JFrame("LabelToRoi - ROI erotion")
frame3.setLocation(100,100)
frame3.setSize(450,250)
frame3.setLayout(None)


def f3_clic_update(event):
   print("Click Update")
   RoiEroder(int(f3_txt1.getText()))


def f3_clic_SaveROIs(event):
   RM = RoiManager()        # we create an instance of the RoiManager class
   rm = RM.getRoiManager()
   pixels = gvars['eroded_pixels']
   path_to_updated_ROIs = str(gvars['path_original_image'].replace(".tif", "") + "_Erosion_" +str(pixels)+ "px_" + "RoiSet.zip")
   rm.runCommand("Save", path_to_updated_ROIs)
   print("ROIs saved")
   print pixels

   #Save Outline Images
   imp = gvars["workingImage"]
   path_to_simple_outline = str(gvars['path_original_image'].replace(".tif", "") + "_Erosion_" +str(pixels)+ "px_" + "Outlines.jpg")
   outlines_image = imp.flatten()
   IJ.saveAs(outlines_image, "JPG", path_to_simple_outline)

   JOptionPane.showMessageDialog(None, "ROIs saved to:\n%s\nOutline image saved to:\n%s" % (path_to_updated_ROIs, path_to_simple_outline))


def f3_clic_measurements(event):
   print "Click Set Measurements"
   IJ.run("Set Measurements...", "")

def f3_clic_saveTable(event):
   print "Click Save Table"
   RM = RoiManager()        # we create an instance of the RoiManager class
   rm = RM.getRoiManager()
   imp = gvars["workingImage"]
   table_message = []
   is_scaled = imp.getCalibration().scaled()
   if not is_scaled:
      JOptionPane.showMessageDialog(None, "Warning: your image is not spatially calibrated. \nTo calibrate, go to Analyze > Set Scale...")

   nChannels = imp.getNChannels()

   print "Total channels:"
   print nChannels
   for current_channel in range(1,nChannels+1):
      print "Current channel:"
      print current_channel

      imp.setSlice(current_channel)
      current_slice = str(imp.getCurrentSlice()) #Get current slice for saving into filename
      print "Current slice:"
      print current_slice

      is_scaled = imp.getCalibration().scaled()
      if is_scaled:
          spatial_cal = "True"
      else:
          spatial_cal = "False"

      IJ.run("Clear Results", "")
      rm.runCommand(imp,"Select All");
      rm.runCommand(imp,"Measure")

      table = ResultsTable.getResultsTable().clone()
      IJ.selectWindow("Results")
      IJ.run("Close")

      filename = os.path.split(gvars["path_original_image"])[1]
      print filename

      pixels = gvars['eroded_pixels'] #To save number of eroded pixels in table and table name

      for i in range(0, table.size()):
         table.setValue('File', i, str(filename))
         table.setValue('Channel', i, current_channel)
         table.setValue('Pixels_eroded', i, str(pixels))
         table.setValue('Spatial_calibration', i, spatial_cal)

      table.show("Tabla actualizada")


      path_to_table = str(gvars['path_original_image'].replace(".tif", "") + "_Erosion_" +str(pixels)+ "px_Channel_" + str(current_channel) + ".csv")

      IJ.saveAs("Results", path_to_table)
      table_message.append("Table saved to %s" % path_to_table)

      path_to_multichannel_table = str(gvars['path_original_image'].replace(".tif", "") + "_Erosion_" +str(pixels)+ "px_AllChannels" + ".csv")


      try:
          if current_channel ==1:
            multichannel_table_file = open(path_to_multichannel_table, 'w')
            current_table =  open(path_to_table, 'r')
            first_line = next(current_table)
            multichannel_table_file.writelines(first_line)
            multichannel_table_file.close()
            current_table.close()

          with open(path_to_multichannel_table, 'a') as multichannel_table_file, open(path_to_table, 'r') as current_table:
             _ = next(current_table) # To avoid appending the header again and again in every iteration
             for line in current_table:
                multichannel_table_file.writelines(line)

      except IOError as e:
         JOptionPane.showMessageDialog(None, "Error: The file %s is open.\nPlease close it and try again!" % path_to_multichannel_table)
         print e
         return #Stop running

   JOptionPane.showMessageDialog(None, "\n".join(table_message))


def f3_clic_prev(event):
   frame2.setVisible(True)
   frame3.setVisible(False)
   progressBar.value = 0
   gvars["workingImage"].close() # When going back, close the current picture
   gvars['eroded_pixels'] = 0
   f2_txt1.setText("") # I reset the previously browsed images in case of going back to the main frame
   f2_txt2.setText("")
   del gvars['path_original_image']
   del gvars['path_label_image']

def f3_clic_finish(event): # TERMINAR
   print "Click Finish"
   gvars["workingImage"].close() # When going back, close the current picture
   frame3.dispose()



# Number of pixels to erode
lbl1 = JLabel("Number of pixels to erode")
lbl1.setBounds(110,30,160,20)
f3_txt1 = JTextField(10)
f3_txt1.setBounds(270, 30, 60,20)
f3_txt1.setText(str(0))


# Button Update
f3_btn_update = JButton("Update ROIs", actionPerformed = f3_clic_update)
f3_btn_update.setBounds(60,70,150,20)

# Button Save Rois
f3_btn_saveRois = JButton("Save ROIs", actionPerformed = f3_clic_SaveROIs)
f3_btn_saveRois.setBounds(250,70,150,20)

# Button Previous - Choose Parameters
f3_btn_params = JButton("Set measurements", actionPerformed = f3_clic_measurements)
f3_btn_params.setBounds(60,110,150,20)

# Button Previous - Save Table
f3_btn_saveTable = JButton("Save CSV Table", actionPerformed = f3_clic_saveTable)
f3_btn_saveTable.setBounds(250,110,150,20)

# Button Previous
f3_btn_prev = JButton("Previous", actionPerformed = f3_clic_prev)
f3_btn_prev.setBounds(60,150,150,20)

# Button Finish
f3_btn_finish = JButton("Finish", actionPerformed = f3_clic_finish)
f3_btn_finish.setBounds(250,150,150,20)

frame3.add(lbl1)
frame3.add(f3_txt1)

frame3.add(f3_btn_update)
frame3.add(f3_btn_saveRois)
frame3.add(f3_btn_params)
frame3.add(f3_btn_saveTable)
frame3.add(f3_btn_prev)
frame3.add(f3_btn_finish)



frame3.setVisible(False)

###########################################################
#########  Window #4: Multiple Images #####################
###########################################################

frame4 = JFrame("LabelToRoi - Multiple Images: Choose directory")
frame4.setLocation(100,100)
frame4.setSize(450,220)
frame4.setLayout(None)


def f4_clic_browse1(event):
   print("Click browse 1")
   fc = JFileChooser()
   fc.setCurrentDirectory(gvars['path_JFileChooser'])
   fc.setDialogTitle('Select Directory for multiple images')
   fc.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY)

   result = fc.showOpenDialog( None )
   if result == JFileChooser.APPROVE_OPTION :
      if fc.getSelectedFile().isDirectory():
         message = 'Path to original image %s' % fc.getSelectedFile()
         gvars['path_multiple_image_directory'] = str(fc.getSelectedFile())
         f4_txt1.setText(gvars['path_multiple_image_directory'])
         gvars['path_JFileChooser'] = fc.getSelectedFile()

   else :
      message = 'Request canceled by user'
   print( message )

def f4_clic_prev(event):
   frame1.setVisible(True)
   frame4.setVisible(False)

   if 'path_multiple_image_directory' in gvars:
       del gvars['path_multiple_image_directory']
       f4_txt1.setText("")
       f4_lbl3.setText("")


def f4_clic_next(event):
   if 'path_multiple_image_directory' not in gvars:
      JOptionPane.showMessageDialog(None, "You have to choose the image directory")

   else:
      multiple_path = gvars['path_multiple_image_directory']
      files = [f for f in listdir(multiple_path) if isfile(join(multiple_path, f))]


      pixels_to_erode = int(f4_txt2.getText())
      task = LabelToRoi_Multiple_Task(files,pixels_to_erode,label_update_fun) # Executes the LabelToRoi function defined on top of this script. It is wrapped into a SwingWorker in order for the windows not to freeze
      task.addPropertyChangeListener(update_progress_multiple) # To update the progress bar
      task.execute()

       ### progress label
      f4_lbl3.setVisible(True)



def update_progress_multiple(event):
   # Invoked when task's progress property changes.
   if event.propertyName == "progress":
        f4_progressBar.value = event.newValue

def label_update_fun(current_label, total_labels):
    f4_lbl3.setText("Processing image %i/%i" % (current_label, total_labels))


def f4_clic_measurements(event):
   print "Click Set Measurements"
   IJ.run("Set Measurements...", "")

# Browse original image
f4_lbl1 = JLabel("Path to directory:")
f4_lbl1.setBounds(40,20,200,20)
f4_btn_directory = JButton("Browse", actionPerformed = f4_clic_browse1)
f4_btn_directory.setBounds(170,20,100,20)
f4_txt1 = JTextField(10)
f4_txt1.setBounds(280, 20, 120,20)

# Number of pixels to erode
f4_lbl2 = JLabel("Number of pixels to erode")
f4_lbl2.setBounds(40,50,160,20)
f4_txt2 = JTextField(10)
f4_txt2.setBounds(280, 50, 120,20)
f4_txt2.setText(str(0))

# Processing image label
f4_lbl3 = JLabel("")
f4_lbl3.setBounds(40,75,200,20)
f4_lbl3.setVisible(True)

# Progress Bar
f4_progressBar = JProgressBar(0, 100, value=0, stringPainted=True)
f4_progressBar.setBounds(40,100,360,20)

# Button Set Measurements
f4_btn_params = JButton("Set measurements", actionPerformed = f4_clic_measurements)
f4_btn_params.setBounds(145,135,150,20)

# Button Previous
f4_btn_prev = JButton("Previous", actionPerformed = f4_clic_prev)
f4_btn_prev.setBounds(40,135,100,20)

# Button Next
f4_btn_next = JButton("Run", actionPerformed = f4_clic_next)
f4_btn_next.setBounds(300,135,100,20)



frame4.add(f4_lbl1)
frame4.add(f4_btn_directory)
frame4.add(f4_txt1)

frame4.add(f4_lbl2)
frame4.add(f4_txt2)

frame4.add(f4_lbl3)

frame4.add(f4_btn_params)

frame4.add(f4_btn_prev)
frame4.add(f4_btn_next)

frame4.add(f4_progressBar)

frame4.setVisible(False)
