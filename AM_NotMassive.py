'''
AM_NotMassive

"I can't believe it's not Massive!"
A nuke crowd simulator by Art and Math

@darkness - Daniel Harkness

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
'''

import uuid
import os
import random
import colorsys
import nuke
import nukescripts

''' methods run on callbacks '''

def respondToInputChange(group):
    '''
    this method is run on a knobChanged callback
    it adds image inputs if needed
    deletes timage inputs of there are supurluous image imputs available
    AFTER the last connected input
    '''
    with group:
        print 'input changed'
        # add a new input if we run out of image inputs

        lastImgInput = nuke.toNode('img1')
        lastImgInputNumber = 1
        allInputs = []
        for inp in nuke.allNodes('Input'):
            allInputs.append(inp)
            if 'img' in inp['name'].value():
                lastImgInputNumber = lastImgInputNumber+1
                if int(inp['name'].value()[3:]) > int(lastImgInput['name'].value()[3:]):
                    lastImgInput = inp
            
        print 'last input name: %s' % ( lastImgInput['name'].value() )
        print 'last input number: %s' % ( lastImgInputNumber )

        prefs = nuke.toNode('preferences')
        gridWidth = prefs['GridWidth'].value()

        # add new input if we have run out
        if group.input(lastImgInputNumber) is not None:
            newInputName = str(int(lastImgInput['name'].value()[3:])+1)
            print 'creating new input: img%s' % ( newInputName )
            newInput = nuke.createNode('Input', inpanel = False)
            newInput['name'].setValue( 'img%s' % ( newInputName) )
            newInput['label'].setValue('input [value number]')

            newInput.setXpos( int( lastImgInput['xpos'].value() + gridWidth ))
            newInput.setYpos( int( lastImgInput['ypos'].value() ))
            print 'created new input: img%s' % ( newInputName )

        # remove inputs if there are too many unconnected
        elif group.input(lastImgInputNumber-1) is None and lastImgInputNumber != 2:
            print 'there are extra inputs we don\'t need, let\'s delete them'
            indexOfNodesToDelete = []
            haveFoundLastConnectedImage = False
            while haveFoundLastConnectedImage is False:
                indexOfNodesToDelete.append ( lastImgInputNumber )
                lastImgInputNumber = lastImgInputNumber-1
                if group.input(lastImgInputNumber-1) is not None:
                    # some safety checking here to make sure img1 doesn't get caught up in the delete list
                    if lastImgInputNumber == 1:
                        indexOfNodesToDelete.pop()
                    haveFoundLastConnectedImage = True
            print 'input numbers of the inputs to delete: %s' % ( indexOfNodesToDelete )
            for i in range (len(indexOfNodesToDelete) ):
                nodeToDelete = nuke.toNode ( 'img%s' % (indexOfNodesToDelete[i]-1) )
                print 'deleting input: %s' % ( nodeToDelete.name() )
                nuke.delete ( nodeToDelete )

        # do nothing
        else:
            print 'no change to inputs'

def respondToKnobChange(knob,group):
    ''' disable and enable some knobs as needed '''

    # 'Use saved vertex selection' checkbox checked/unchecked
    if knob.name() == 'useSelection':
        if group['useSelection'].value():
            group['saveSelection'].setEnabled(True)
            group['restoreSelection'].setEnabled(True)
        else:
            group['saveSelection'].setEnabled(False)
            group['restoreSelection'].setEnabled(False)

    # 'Randomize vertices' checkbox checked/unchecked
    elif knob.name() == 'vertexRandom':
        if group['vertexRandom'].value():
            group['vertexSeed'].setEnabled(True)
        else:
            group['vertexSeed'].setEnabled(False)

    # 'Randomize vertices' checkbox checked/unchecked
    elif knob.name() == 'vertexStep':
        if knob.value() < 1:
            nuke.message ('The vertexStep value must be 1 or greater.\n\nSetting vertexStep to 1.')
            group['vertexStep'].setValue(1)

    # 'Input order' pulldown changed
    elif knob.name() == 'inputOrder':
        if group['inputOrder'].value() == 'Random':
            group['inputSeed'].setEnabled(True)
            group['inputSeed'].setVisible(True)
            group['duplicationRadius'].setEnabled(False)
            group['duplicationRadius'].setVisible(False)
            group['duplicationRadiusSeed'].setEnabled(False)
            group['duplicationRadiusSeed'].setVisible(False)
        elif group['inputOrder'].value() == 'Duplication radius':
            group['inputSeed'].setEnabled(False)
            group['inputSeed'].setVisible(False)
            group['duplicationRadius'].setEnabled(True)
            group['duplicationRadius'].setVisible(True)
            group['duplicationRadiusSeed'].setEnabled(True)
            group['duplicationRadiusSeed'].setVisible(True)
            nuke.message ('Duplication radius is not yet implemented. Currently it behaves the same as Input Order: Step')
        else:
            group['inputSeed'].setEnabled(False)
            group['inputSeed'].setVisible(False)
            group['duplicationRadius'].setEnabled(False)
            group['duplicationRadius'].setVisible(False)
            group['duplicationRadiusSeed'].setEnabled(False)
            group['duplicationRadiusSeed'].setVisible(False)

    # 'randomize' checkbox for time offset checked/unchecked
    elif knob.name() == 'timeOffsetRandomize':
        if group['timeOffsetRandomize'].value():
            group['timeOffsetStep'].setEnabled(False)
            group['timeOffsetSeed'].setEnabled(True)
        else:
            group['timeOffsetStep'].setEnabled(True)
            group['timeOffsetSeed'].setEnabled(False)

    # 'mirror' checkbox for time offset checked/unchecked
    elif knob.name() == 'mirror':
        if group['mirror'].value():
            group['mirrorSeed'].setEnabled(True)
        else:
            group['mirrorSeed'].setEnabled(False)

    # knob is invisible last in the list and only called when
    # right click setKnobsToDefault happens
    elif knob.name() == 'setKnobsToDefault':
        setDefaultValues(group)

def setDefaultValues(group):
    '''
    Default values for the group so that right click
    and setting default values works
    '''
    print 'Resetting to default values'
    group['vertexStep'].setValue(1)
    group['startVertex'].setValue(0)
    group['useSelection'].setValue(False)
    group['vertexRandom'].setValue(False)
    group['inputOrder'].setValue(0)
    group['pivotOffset'].setValue(-0.5)
    group['scale'].setValue(10)
    group['scaleVariation'].setValue(0)
    group['scaleSeed'].setValue(0)
    group['positionOffset'].setValue([0,0,0])
    group['positionOffsetXZseed'].setValue(0)
    group['positionOffsetYseed'].setValue(0)
    group['timeOffset'].setValue(0)
    group['timeOffsetStep'].setValue(0)
    group['vertexStep'].setValue(1)
    group['timeOffsetRandomize'].setValue(True)
    group['timeOffsetSeed'].setValue(0)
    group['mirror'].setValue(False)
    group['mirrorSeed'].setValue(0)
    group['aov_randomSeed'].setValue(0)
    group['displayAOVs'].setValue(True)
    group['displayPercentage'].setValue(100)
    group['displayPercentOffset'].setValue(0)
    group['look_axis'].setValue(0)
    group['look_rotate_x'].setValue(True)
    group['look_rotate_y'].setValue(True)
    group['look_rotate_z'].setValue(True)
    group['look_strength'].setValue(1)
    group['look_use_quaternions'].setValue(False)
    group['vertexStore'].setValue('')
    group['label'].setValue('No Crowd')

    '''
    set this hidden text to true and it will get flipped back to default
    when artist right clicks to set defaults, calling this method
    '''
    group['setKnobsToDefault'].setValue('True')

    removePreviousScene (group)

''' crowd creation methods '''

def everyNthPointOfPoints (allPoints,group):
    # return only the points we want to attach cards to
    vertexStep = int(group['vertexStep'].value())
    i = int(group['startVertex'].value())
    lastRangeItem = i

    emissionPoints = []
    while i < len(allPoints):
        emissionPoints.append(allPoints[i])

        if group['vertexRandom'].value():
            random.seed(int(group['vertexSeed'].value())+i)                
            i = lastRangeItem + random.randint(1, vertexStep*2)
            lastRangeItem = i
        else:
            i = i + vertexStep

    return emissionPoints

def verticesFromInput(group):
    ''' return the points in the emitter geo that we want to stick cards to '''

    # change temp dir if needed
    # defaulting to nuke's temp dir, not sure how kosher this is 
    tmpDirRoot = os.environ.get('NUKE_TEMP_DIR')
    
    # give emitter geo a unique filename so that nuke won't use a cached version
    emitterFileBase = str(uuid.uuid4())
    tmpDir = '%s/CrowdControl' % (tmpDirRoot)
    
    try:
        os.mkdir(tmpDir)
    except:
        pass
    tmpPath = '%s/%s.obj' % (tmpDir,emitterFileBase)

    pythonGeoIn = nuke.toNode('EmitterPythonGeoIn')
    selectedPoints = pythonGeoIn['geo'].getSelection()
    
    # write out a file to read vertices from
    writeGeo = nuke.toNode('WriteEmitterGeo')
    writeGeo['file'].setValue( tmpPath )
    nuke.execute(writeGeo['name'].value(), nuke.frame(), nuke.frame())
    
    # read it back in and we get true vertiex positions in the PythonGeo node
    readGeo = nuke.toNode('ReadEmitterGeo')
    readGeo['file'].setValue( tmpPath )
    
    # get a list of vertices
    pythonGeoOut = nuke.toNode('EmitterPythonGeoOut')
    allTheGeo = pythonGeoOut['geo'].getGeometry()
    theGeoObj = allTheGeo[0]
    vList = theGeoObj.points()
    
    # remove the temp file, we no longer need it
    os.remove(tmpPath)
    
    # convert the list of vertices into a list of points
    allPoints = []
    p = []
    for v in vList:
        p.append(v)
        if len(p)==3:
            allPoints.append(p)
            p = []

    return allPoints

def imageInputList(group):
    '''
    iterate through the image inputs and return list of connected dots
    for image inputs that actually have images connected
    '''

    # pity the fool who doesn't use default node graph preferences
    prefs = nuke.toNode('preferences')
    gridWidth = prefs['GridWidth'].value()
    gridHeight = prefs['GridHeight'].value()

    switchInputs = []
    for inp in nuke.allNodes('Input'):
        inpNumber = int(inp['number'].value())
        if 'img' in inp.name():
            dot = nuke.createNode('Dot', inpanel = False)
            dot['name'].setValue(inp['name'].value().replace('img','dot'))
            dot.setXpos(int(inp['xpos'].value()+inp.screenWidth()/2-dot.screenWidth()/2))
            dot.setYpos(int(inp['ypos'].value()+gridHeight*5))
            dot.setInput(0,inp)

            if group.input(inpNumber) is not None:
                switchInputs.append(dot.name())
                dot.setYpos(int(inp['ypos'].value()+gridHeight*10))

    switchInputs = sorted(switchInputs)
    print 'valid image inputs: %s' % (switchInputs)
    return switchInputs

def saveSelectedVertices(group):
    ''' Save the selected points in the 3D viewer '''

    snap3dPoints = nukescripts.snap3d.selectedPoints()
    points = []

    for point in snap3dPoints:
       points.append(point)

    # prep points for storage
    pointsStr = str(points)[1:-1]
    pointsStr = pointsStr.replace(' ','')
    pointsStr = pointsStr.replace('},{','}|{')

    # store the points in a hidden field
    print 'Saving points: %s' % (pointsStr)
    group['vertexStore'].setValue(pointsStr)
   
def retrieveSavedVertices(group):
    ''' retrieve the stored points '''

    pointsStr = group['vertexStore'].value()

    # retrieve points from storage as sting and convert back to real points
    newPointsList = []
    newPointsSplit = pointsStr.split('|')
    for newPointStr in set(newPointsSplit):
       newPointStr = newPointStr[1:-1]
       newPointSplit = newPointStr.split(',')
       newPoint = []
       for item in newPointSplit:
           newPoint.append(float(item))
       newPointsList.append(newPoint)

    print 'retrieved points: %s' % (newPointsList)
    return newPointsList

def removePreviousScene(group):
    ''' clean up the inside of the gizmo if it has been used already '''

    with group:
        nodesToKeep = []

        # keep the core nodes
        for n in nuke.allNodes():
            if 'keepOnExecute' in n.knobs().keys():
                nodesToKeep.append(n)
        
        # keep the inputs
        for inp in nuke.allNodes('Input'):
            nodesToKeep.append(inp)
        print 'keeping nodes: %s\n' % ( nodesToKeep )

        # remove the previous scene
        nodesDeleted = []
        for n in nuke.allNodes():
            
            if n not in nodesToKeep:
                nodesDeleted.append (n.name())
                nuke.delete(n)
        print 'deleted nodes: %s\n' % ( nodesDeleted )

        # disconnect everything from the scene node
        scene = nuke.toNode('scene')
        for i in range(0,scene.inputs()):
            scene.setInput(i,None)

def makeCrowd(group):
    ''' Atists hits make crowd button and we make a crowd '''

    with group:
        # get a list of points we want to creat cards on
        points = []
        if group['useSelection'].value() and len(group['vertexStore'].value())>0:
            allPoints = retrieveSavedVertices(group)
            points = everyNthPointOfPoints(allPoints,group)
        else:
            allPoints = verticesFromInput(group)
            points = everyNthPointOfPoints(allPoints,group)

        cardWarningLevel = 500
        if len(points) > cardWarningLevel:
            if not nuke.ask('Are you sure you want to create %s cards? This may take a long time...' % (len(points))):
                return

        #delete the old scene
        removePreviousScene (group)

    with group:
        # pity the fool who doesn't use default node graph preferences
        prefs = nuke.toNode('preferences')
        gridWidth = prefs['GridWidth'].value()
        gridHeight = prefs['GridHeight'].value()
        
        lookDot = nuke.toNode('lookDot')
        img1 = nuke.toNode('img1')
        lastXY = [img1['xpos'].value()-gridWidth,img1['ypos'].value()]
        lookDot.setYpos(int(lastXY[1]+gridHeight*76))

        switchInputs = imageInputList(group)
        
        # make channels, channel strings are used later in node creation
        crowdRandomColorStr = 'crowdRandomColor'
        nuke.Layer( crowdRandomColorStr , ['red', 'green', 'blue'] )

        crowdIDStr = 'crowdID'
        nuke.Layer( crowdIDStr, ['id','sprite'] )

        '''
        crowdCharacterMaskStr = 'crowdCharacterMask'
        nuke.Layer( crowdCharacterMaskStr , ['alpha'] )
        '''

        crowdMirrorMaskStr = 'crowdMirrorMask'
        nuke.Layer( crowdMirrorMaskStr , ['alpha'] )

        transformGeoList = []
        cardList = []
        whichInput = 0

        for i in range(len(points)):
            point = points[i]

            # make a switch to plug in the image inputs
            inputSwitch = nuke.createNode('Switch', inpanel = False)
            inputSwitch.setName('imgSwitch')
            inputSwitch['label'].setValue('which: [value which]\nauto-generated')
            inputSwitch.setXpos(int(lastXY[0]+gridWidth))
            inputSwitch.setYpos(int(lastXY[1]+gridHeight*20))

            for j in range(len(switchInputs)):
                inputSwitch.setInput(j,nuke.toNode(switchInputs[j]))

            # Input switch to chose what images appear on what cards
            # TODO: Make a a fucntion for Duplication radius
            inputFromDuplicationRadius = whichInput
            ifStepExpr = '[string match [value inputOrder] "Step"]?%s' % (whichInput)
            ifRandomExpr = '[string match [value inputOrder] "Random"]?'\
                'rint(random(%s+%s,1)*%s)' % ('parent.inputSeed', i, len(switchInputs)-1)
            inputSwitch['which'].setExpression('%s:%s:%s' % (ifStepExpr, ifRandomExpr, str(inputFromDuplicationRadius)))
            whichInput = whichInput+1
            if whichInput >= len(switchInputs):
                whichInput = 0

            '''
            # make the id channel
            idShuffle = nuke.createNode('Shuffle', inpanel = False)
            idShuffle.setName('aov_idShuffle')
            idShuffle['in'].setValue('none')
            idShuffle['out'].setValue(crowdIDStr)
            idShuffle['label'].setValue('([value out])\nauto-generated')
            idShuffle['disable'].setExpression('!parent.displayAOVs')
            idShuffle.setXpos(int(lastXY[0]+gridWidth))
            idShuffle.setYpos(int(lastXY[1]+gridHeight*30))

            # make the id mult
            idKnob = nuke.Int_Knob('ID','ID')
            idKnob.setValue(i)

            idMult = nuke.createNode('Multiply' ,inpanel = False)
            idMult.addKnob( idKnob )
            idMult.setName('aov_idMult')
            idMult['channels'].setValue(crowdIDStr)
            idMult['value'].setSingleValue(True)
            idMult['value'].setExpression('%s' % ('this.ID+1'))
            #idMult['maskChannelInput'].setValue('rgba.alpha')
            idMult['label'].setValue('auto-generated')
            idMult['disable'].setExpression('!parent.aov_id')
            idMult.setXpos(int(lastXY[0]+gridWidth))
            idMult.setYpos(int(lastXY[1]+gridHeight*32))
            '''

            # make the id expression
            idExpr = nuke.createNode('Expression' ,inpanel = False)
            idExpr.setName('aov_idExpr')
            idExpr['temp_name0'].setValue('id')
            idExpr['temp_expr0'].setValue(str(i))
            idExpr['temp_name1'].setValue('inp')
            idExpr['temp_expr1'].setValue('[value %s.which]' % inputSwitch.name())
            idExpr['channel0'].setValue(crowdIDStr)
            idExpr['channel0'].enableChannel(0,True)
            idExpr['channel0'].enableChannel(1,False)
            idExpr['channel0'].enableChannel(2,False)
            idExpr['expr0'].setValue('id*rgba.alpha')
            idExpr['channel1'].setValue(crowdIDStr)
            idExpr['channel1'].enableChannel(0,False)
            idExpr['channel1'].enableChannel(1,True)
            idExpr['channel1'].enableChannel(2,False)
            idExpr['expr1'].setValue('inp*rgba.alpha')
            idExpr['channel2'].setValue('none')
            idExpr['channel3'].setValue('none')
            idExpr['label'].setValue('auto-generated')
            idExpr['disable'].setExpression('!parent.displayAOVs')
            idExpr.setXpos(int(lastXY[0]+gridWidth))
            idExpr.setYpos(int(lastXY[1]+gridHeight*30))

            # make the grade layer which shuffles in the alpha
            randomShuffle = nuke.createNode('Shuffle', inpanel = False)
            randomShuffle.setName('aov_randomShuffle')
            randomShuffle['in'].setValue('alpha')
            randomShuffle['out'].setValue(crowdRandomColorStr)
            randomShuffle['label'].setValue('([value out])\nauto-generated')
            randomShuffle['disable'].setExpression('!parent.displayAOVs')
            randomShuffle.setXpos(int(lastXY[0]+gridWidth))
            randomShuffle.setYpos(int(lastXY[1]+gridHeight*40))

            # make the grade layer mult
            randomColorMult = nuke.createNode('Multiply' ,inpanel = False)
            randomColorMult.setName('aov_randomMult')
            randomColorMult['channels'].setValue(crowdRandomColorStr)
            randomColorMult['value'].setSingleValue(False)
            randomColorMult['value'].setExpression('random(%s+%s,1)' % ('parent.aov_randomSeed',str(i+0)),0)
            randomColorMult['value'].setExpression('random(%s+%s,1)' % ('parent.aov_randomSeed',str(i+1)),1)
            randomColorMult['value'].setExpression('random(%s+%s,1)' % ('parent.aov_randomSeed',str(i+2)),2)
            randomColorMult['unpremult'].setValue('rgba.alpha')
            randomColorMult['label'].setValue('auto-generated')
            randomColorMult['disable'].setExpression('!parent.displayAOVs')
            randomColorMult.setXpos(int(lastXY[0]+gridWidth))
            randomColorMult.setYpos(int(lastXY[1]+gridHeight*42))

            # make the character mask which can be used for lighting
            '''
            charMaskShuffle = nuke.createNode('Shuffle', inpanel = False)
            charMaskShuffle['in'].setValue('alpha')
            charMaskShuffle['out'].setValue(crowdCharacterMaskStr)
            charMaskShuffle['label'].setValue('([value out])\nauto-generated')
            charMaskShuffle.setXpos(int(lastXY[0]+gridWidth))
            charMaskShuffle.setYpos(int(lastXY[1]+gridHeight*40))
            '''

            # make the mirror mask which can be used for flipping AOVs
            mirrorMaskShuffle = nuke.createNode('Shuffle', inpanel = False)
            mirrorMaskShuffle.setName('aov_mirrorShuffle')
            mirrorMaskShuffle['in'].setValue('alpha')
            mirrorMaskShuffle['out'].setValue(crowdMirrorMaskStr)
            mirrorMaskShuffle['label'].setValue('([value out])\nauto-generated')
            mirrorMaskShuffle['disable'].setExpression('!parent.displayAOVs')
            mirrorMaskShuffle.setXpos(int(lastXY[0]+gridWidth))
            mirrorMaskShuffle.setYpos(int(lastXY[1]+gridHeight*50))

            # make the mirror for flopping random cards
            idKnob = nuke.Int_Knob('mirrorID','mirrorID')
            idKnob.setValue(i)

            flop = nuke.createNode('Mirror2', inpanel = False)
            flop.addKnob( idKnob )
            flop['flop'].setValue(True)
            flop['disable'].setExpression('parent.mirror?random(this.mirrorID+parent.mirrorSeed,1)>0.5?1:0:1')
            flop['label'].setValue('auto-generated')
            flop.setXpos(int(lastXY[0]+gridWidth))
            flop.setYpos(int(lastXY[1]+gridHeight*52))

            # make the mirror mask mult which can be used for flipping AOVs
            mirrorMaskMult = nuke.createNode('Multiply', inpanel = False)
            mirrorMaskMult.setName('aov_mirrorMult')
            mirrorMaskMult['channels'].setValue(crowdMirrorMaskStr)
            mirrorMaskMult['value'].setValue(0)
            mirrorMaskMult['disable'].setExpression('parent.displayAOVs?!input0.disable:1')
            mirrorMaskMult['label'].setValue('(auto-generated')
            mirrorMaskMult.setXpos(int(lastXY[0]+gridWidth))
            mirrorMaskMult.setYpos(int(lastXY[1]+gridHeight*54))

            # make the time offset
            idKnob = nuke.Int_Knob('offsetID','offsetID')
            idKnob.setValue(i)

            timeOffset = nuke.createNode('TimeOffset', inpanel = False)
            timeOffset.addKnob( nuke.Tab_Knob('User') )
            timeOffset.addKnob( idKnob )
            timeOffsetRandomizeExpr = 'rint(random(parent.timeOffsetSeed+%s,1)*parent.timeOffset*2-parent.timeOffset)' % ('this.offsetID')
            timeOffsetStepExpr = 'parent.timeOffset?parent.timeOffsetStep*this.offsetID%abs(parent.timeOffset):0'
            timeOffset['time_offset'].setExpression('parent.timeOffsetRandomize?%s:%s' % (timeOffsetRandomizeExpr,timeOffsetStepExpr))
            timeOffset['label'].setValue('[value time_offset] frames\nauto-generated')
            timeOffset.setXpos(int(lastXY[0]+gridWidth))
            timeOffset.setYpos(int(lastXY[1]+gridHeight*60))


            # make the card
            idKnob = nuke.Double_Knob('cardID','cardID')
            idKnob.setRange(0,100)
            idOffsetKnob = nuke.Double_Knob('cardIDOffset','cardIDOffset')
            idOffsetKnob.setRange(0,100)

            card = nuke.createNode('Card', inpanel = False)
            card.addKnob( nuke.Tab_Knob('User') )
            card.addKnob( idKnob )
            card.addKnob( idOffsetKnob )
            card['cardIDOffset'].setExpression('parent.displayPercentOffset+this.cardID<=100?'\
                'parent.displayPercentOffset+this.cardID:this.cardID-100+parent.displayPercentOffset')
            card['disable'].setExpression('$gui?parent.displayPercentage<100?parent.displayPercentage>this.cardIDOffset?0:1:0:1')
            card.setXpos(int(lastXY[0]+gridWidth))
            card.setYpos(int(lastXY[1]+gridHeight*70))
            cardList.append(card)
        
            # make the transform geo
            transformGeo = nuke.createNode('TransformGeo', inpanel = False)
            transformGeo.setXpos(int(lastXY[0]+gridWidth))
            transformGeo.setYpos(int(lookDot['ypos'].value()))            
            transformGeo.setInput(0,card)
            transformGeo.setInput(2,lookDot)
            transformGeo['translate'].setExpression('random(%s+%s,1)*parent.positionOffset(0)' \
                '-parent.positionOffset(0)/2+%s' % ('parent.positionOffsetXZseed',str(i+0),point[0]),0)
            transformGeo['translate'].setExpression('random(%s+%s,1)*parent.positionOffset(1)' \
                '-parent.positionOffset(1)/2+%s' % ('parent.positionOffsetYseed',str(i+1),point[1]),1)
            transformGeo['translate'].setExpression('random(%s+%s,1)*parent.positionOffset(2)' \
                '   -parent.positionOffset(2)/2+%s' % ('parent.positionOffsetXZseed',str(i+2),point[2]),2)
            transformGeo['pivot'].setExpression('parent.pivotOffset',1)
            transformGeo['uniform_scale'].setExpression('parent.scale+random(%s+%s,1)*' \
                '(scaleVariation*parent.scale)-(scaleVariation*parent.scale)/2' % ('parent.scaleSeed', str(i)))
            transformGeo['look_axis'].setExpression('parent.look_axis')
            transformGeo['look_rotate_x'].setExpression('parent.look_rotate_x')
            transformGeo['look_rotate_y'].setExpression('parent.look_rotate_y')
            transformGeo['look_rotate_z'].setExpression('parent.look_rotate_z')
            transformGeo['look_strength'].setExpression('parent.look_strength')
            transformGeo['look_use_quaternions'].setExpression('parent.look_use_quaternions')

            transformGeoList.append(transformGeo)
        
            lastXY = [ lastXY[0]+gridWidth, lastXY[1]]
            
        # pipe up all the transform geos into the output scene
        scene = nuke.toNode('scene')
        for i in range(len(transformGeoList)):
            scene.setInput(i,transformGeoList[i])
        scene.setYpos(int(lookDot['ypos'].value()+gridHeight*10))    
        nuke.toNode('Output').setYpos(int(lookDot['ypos'].value()+gridHeight*20))    

        # set up the cards so that they can be culled by a percentage in the gui
        random.seed(int(group['vertexStep'].value()))   
        random.shuffle(cardList)
        for i in range(0,len(cardList)):
            cardID = float(i)*100/len(cardList)
            cardList[i]['cardID'].setValue(cardID)


        # change the group label and let artist know how many cards were created
        group['label'].setValue('%s Cards' % (len(transformGeoList)))

''' crowd baking methods'''

def hexToRGB(hexCol):
    hex = '%08x' % hexCol 
    r = float(int(hex[0:2], 16))/255.0
    g = float(int(hex[2:4], 16))/255.0
    b = float(int(hex[4:6], 16))/255.0
    #a = [float(int(hex[6:8], 16))/255.0]
    return [r,g,b]

def bakeTileColor(node):
    tc_hex = node['tile_color'].value()
    tc_rgb = hexToRGB(tc_hex)
    tc_hsv = colorsys.rgb_to_hsv(tc_rgb[0],tc_rgb[1],tc_rgb[2])
    tc_hsv = [tc_hsv[0],tc_hsv[1],tc_hsv[2]*0.5]
    tc_rgb = colorsys.hsv_to_rgb(tc_hsv[0],tc_hsv[1],tc_hsv[2])
    tc_hex = int('%02x%02x%02x%02x' % (tc_rgb[0]*255,tc_rgb[1]*255,tc_rgb[2]*255,1),16)
    node['tile_color'].setValue( tc_hex )

def keepSceneAndRemoveCrowdGeneratingNodes(group):
    ''' remove noes used to generate the crowd when we bake a crowd '''

    with group:
        nodesToDelete = []

        # remove the core nodes
        for n in nuke.allNodes():
            if 'keepOnExecute' in n.knobs().keys():
                if 'keepOnBake' not in n.knobs().keys():
                    nodesToDelete.append(n)
        
        # remove the nodes
        nodesDeleted = []
        for n in nodesToDelete:
            nodesDeleted.append (n.name())
            nuke.delete(n)
        print 'deleted nodes: %s\n' % ( nodesDeleted )

def remove_user_knobs(node):
    # https://www.mail-archive.com/nuke-python@support.thefoundry.co.uk/msg04880.html
    # @bend
    in_user_tab = False
    to_remove = []
    for n in range(node.numKnobs()):
        cur_knob = node.knob(n)
        is_tab = isinstance(cur_knob, nuke.Tab_Knob)

        # Track is-in-tab state
        if is_tab and cur_knob.name() == "User": # Tab name to remove
            in_user_tab = True
        elif is_tab and in_user_tab:
            in_user_tab = False

        # Collect up knobs to remove later
        if in_user_tab:
            to_remove.append(cur_knob)

    # Remove in reverse order so tab is empty before removing Tab_Knob
    for k in reversed(to_remove):
        node.removeKnob(k)

    # Select first tab
    node.knob(0).setFlag(0)

def bakeCardTree(transformGeoNode):
    n = transformGeoNode
    while 'imgSwitch' not in n.name() :
        for key in n.knobs().keys():
            kn = n.knob(key)
            if kn.hasExpression():
                #with oldGroup:
                #oldNode = nuke.toNode(n.name())
                #oldknob = oldNode.knob(kn.name())
                #v = oldknob.value()
                v = kn.value()
                kn.clearAnimated()
                kn.setValue(v)
        #deal with the expression nodes
        if n.Class() == 'Expression':
            for i in range(0,3):
                e = 'temp_expr%s' % (i)
                n[e].setValue(n[e].value())
        #bake node a golden hue of butter subtitute
        tc_rgb = [1,0.545,0.196]
        tc_hex = int('%02x%02x%02x%02x' % (tc_rgb[0]*255,tc_rgb[1]*255,tc_rgb[2]*255,1),16)
        n['tile_color'].setValue( tc_hex )
        remove_user_knobs(n)
        n = n.dependencies()[0]


    # link up inputs and remove switchs
    switch = n
    if switch.Class() == 'Switch':
        if len (switch.dependent()) > 0:
            downstreamNode = switch.dependent()[0]
            upstreamNode = switch.input(int(switch['which'].value()))

            dot = nuke.createNode('Dot',inpanel = False)
            dot.setName('imgSwitch')
            dot.setSelected(False)
            dot.setXpos(int(switch.xpos()+switch.screenWidth()/2-dot.screenWidth()))
            dot.setYpos(int(switch.ypos()+switch.screenHeight()/2-dot.screenHeight()))
            #for some reason the above positioning is sometimes flakey
            nuke.autoplaceSnap( dot ) 

            dot.setInput(0,upstreamNode)
            downstreamNode.setInput(0,dot)
            nuke.delete(switch)

def bakeSelectedNodes(group,nodes):
    '''
    Baked selected cards
    Turn on the AOVs first if they're not turned on already so we can bake the AOVs in
    restore AOV in GUI state
    '''
    with group:
        v = group['displayAOVs'].value()
        d = group['displayPercentage'].value()
        group['displayAOVs'].setValue(True)
        group['displayPercentage'].setValue(100)

        transformGeoList = []
        for n in nodes:
            while n.Class() != 'TransformGeo':
                if len(n.dependent())>0:
                    n = n.dependent()[0]
                else:
                    print 'missing dependent:%s' % (n.name())
            transformGeoList.append(n)

        for n in set(transformGeoList):
            for s in nuke.allNodes():
                s.setSelected(False)
            bakeCardTree(n)

        group['displayAOVs'].setValue(v)
        group['displayPercentage'].setValue(d)

def bakeGroup(group):
    '''
    Make a copy of the not massive group
    Remove sutff inside the group we don't need
    Remove knobs we don't keed
    Bake the expressions in the group
    '''

    if not nuke.ask('Are you sure you want to bake? This may take a long time...\n\n1 minute per 100 cards is normal.'):
        return

    with group:
        with nuke.thisParent():
            for n in nuke.selectedNodes():
                n.setSelected(False)

            # change temp dir if needed
            # defaulting to nuke's temp dir, not sure how kosher this is 
            tmpDirRoot = os.environ.get('NUKE_TEMP_DIR')
            
            # give cloned node unique filename so that nuke won't use a cached version
            groupFileBase = str(uuid.uuid4())
            tmpDir = '%s/CrowdControl' % (tmpDirRoot)
            
            try:
                os.mkdir(tmpDir)
            except:
                pass
            tmpPath = '%s/%s.nk' % (tmpDir,groupFileBase)

            group.setSelected(True)
            nuke.nodeCopy(tmpPath)

            for n in nuke.selectedNodes():
                n.setSelected(False)

            nuke.nodePaste(tmpPath)
            newGroup = nuke.selectedNode()

            #remove callbacks
            newGroup.knob('knobChanged').setValue('')
            newGroup.knob('onCreate').setValue('')

            #link up the inputs
            for i in range(group.inputs()):
                inputNode = group.input(i)
                if inputNode is not None:
                    newGroup.setInput(i,inputNode)

            #Bake the group internals
            cards = []
            for n in newGroup.nodes():
                if n.Class() == 'Card':
                    cards.append(n)
            bakeSelectedNodes(newGroup,set(cards))
            keepSceneAndRemoveCrowdGeneratingNodes(newGroup)

            #Rename
            newGroupName = '%s_baked' % (group.name())
            newGroup.setName(newGroupName)

            #disable the dynamic knobs
            knobsToKeep = []
            knobsToKeep.append(newGroup['versionInfo'])
 
            newGroup['displayAOVs'].setValue(True)
            newGroup['displayPercentage'].setValue(100)

            values = []
            for key in newGroup.knobs().keys():
                if newGroup.knob(key) not in knobsToKeep:
                    try:
                        newGroup.knob(key).setEnabled(False)
                    except:
                        #not a user knob
                        pass
            versionInfo = newGroup['versionInfo'].value()
            versionInfo = versionInfo.replace('\'s','\'s baked with')
            newGroup['versionInfo'].setValue(versionInfo)

            # pity the fool who doesn't use default node graph preferences
            prefs = nuke.toNode('preferences')
            gridWidth = prefs['GridWidth'].value()
            gridHeight = prefs['GridHeight'].value()

            # position the baked groupp set off from original group
            newGroup.setXpos(int(group.xpos()+gridWidth))
            newGroup.setYpos(int(group.ypos()+gridHeight*2))
    
            bakeTileColor(newGroup)





