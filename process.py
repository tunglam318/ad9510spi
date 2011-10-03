#!/usr/bin/env python
import sys
import vcd2foo

class ad9510spi  (object):

   def __init__(self):
      self.last_c1 = {}      # remember CMD1 (high-order byte of command)
      self.state=None
      self.prev_meaning=None
      self.memory={}

   def newstate(self, prev, input):
      if input['raw'] == 'MOSI':
         state = 'CMD1'
      elif prev == 'CMD1':
         self.last_c1 = input
         state = 'CMD0'
      elif prev == 'CMD0' :
         #print (input)
         #print (last_c1)
         if self.last_c1['bytes'] == 1:
            state = 'DATA0'
         else:
            sys.stderr.write ("Streaming?\n")
            state = 'DATA0'
      elif prev == 'DATA0' :
         state = 'CMD1'
      else:
         state = prev

      return state

   def begin(self):
      self.state = 'CMD1'

   def end(self):
      pass
   def bool_bit(self, str, pos):
      return (str[pos] == '1')

   def interp(self, state, input):
      meaning = {}
      meaning['raw'] = input
      if (input == 'MOSI'):
         return meaning

      if ((state == 'CMD1') or
          (state == 'CMD0') or
          (state == 'DATA0')):
         if len(input) != 8:
            raise ValueError("Expecting strings of 8 bits (as characters).  Got: %s" % repr(input))
        
         if state == 'CMD1':
            meaning['read']     = self.bool_bit(input, 0)
            meaning['bytes']    =  { '00':1,
                                     '01':2,
                                     '10':3,
                                     '11':'Streaming'}[input[1:3]]
            meaning['addr_top'] = input[3:8]
         elif state == 'CMD0':
            meaning['addr_bottom'] = input[0:8]
         elif state == 'DATA0':
            meaning['value'] = input[0:8]
      return meaning

   def think(self, state, input, memory):
      
      action = None

      if state == 'CMD1':
         memory = input
      elif state == 'CMD0':
         # meaning['read']     = memory['read']
         # meaning['bytes']    = memory['bytes']
         #print (memory)
         memory['raw']=memory['raw'] + input['raw']
         addr_str = memory['addr_top'] + input['addr_bottom']
         memory['addr_str']  = addr_str
         memory['addr'] = int(addr_str,2)
         memory['addr_hex'] = hex(memory['addr'])
      elif state == 'DATA0':
         memory['raw']=memory['raw'] + input['raw']
         memory['value']=int(input['value'],2)
         memory['value_hex']=hex(memory['value'])

         action = memory
         memory = {}

      return (memory, action, input)

   def run(self, data):
      for line in data:         
         l = line.strip()
         self.begin()
         while len(l) > 0:
            byte = l[:8]
            l = l[8:]
            meaning = self.interp(self.state, byte)
            next_state = self.newstate(self.state, meaning)            
            (self.memory, action, input) = self.think(self.state, meaning, self.memory)
            #print ((self.state, byte, next_state, input, action))
            print ((byte, action))
            #print ((byte, meaning))
            self.state = next_state
         self.end()

   
def main(argv):
  vcdfile = "./foo.vcd"


  foo = vcd2foo.VcdEater(vcdfile)

  spi = vcd2foo.SPI(CPOL=0, CPHA=1,
            SCLK="revisit_ad9510./ad9510_hw/old_booter/clockEngine/SCLK",
            CSN="revisit_ad9510./ad9510_hw/old_booter/clockEngine/CSN",
            MOSI="revisit_ad9510./ad9510_hw/old_booter/clockEngine/SDIO")
  spi.register(foo.vcd)


  foo.process()
  spi.end()

  print '\n'.join(spi.get_mosi())

   
  p = ad9510spi()
  p.run(spi.get_mosi())

if __name__ == '__main__':
   sys.exit(main(sys.argv))
