datafile = open(__file__[0:__file__.rfind("/")+1] + "textdata")
data = datafile.readlines()
textdata = dict()
newchar = True
for l in range(len(data)):
  line = data[l].rstrip().replace("<space>", " ")
  if newchar == True:
    if len(line)!=1: raise Exception, "Error in text data file, line " + str(l)
    char = line
    textdata[char] = []
    newchar = False
    width = 0
  else:
    if line=="":
      newchar = True
    else:
      row = []
      if width==0: width = len(line)
      elif len(line) != width: raise Exception, "Error in text data file: wrong width"
      for pixel in line:
        if pixel=="#": row += ["\x01"]
        elif pixel==".": row += ["\x00"]
        else: raise Exception, "Error in text data file: unknown symbol in pixel data"
      textdata[char] += [row]
datafile.close()

def getWidth(text, spacing=1):
  global textdata
  text = text.upper()
  width = 0
  for char in text:
    try: width += len(textdata[char][0]) + spacing
    except KeyError: pass
  if width>0: width -= spacing
  return width

def showtext(blthread, text, offset=0, spacing=1):
  global textdata
  text = text.upper()
  data = blthread.width * blthread.height * "\x00"
  for char in text:
    if offset >= blthread.width: break
    try:
      for rownum in range(min(blthread.height, len(textdata[char]))):
        for colnum in range(min(blthread.width-offset, len(textdata[char][0]))):
          if colnum+offset>=0:
            pos = rownum*blthread.width + colnum + offset
            data = data[0:pos] + textdata[char][rownum][colnum] + data[pos+1:]
      offset += len(textdata[char][0]) + spacing
    except KeyError: pass
  blthread.send(data)
