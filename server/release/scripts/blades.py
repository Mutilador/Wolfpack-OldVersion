#################################################################
#   )      (\_     # WOLFPACK 13.0.0 Scripts                    #
#  ((    _/{  "-;  # Created by: DarkStorm                      #
#   )).-' {{ ;'`   # Revised by:                                #
#  ( (  ;._ \\ ctr # Last Modification: Created                 #
#################################################################
# Script for bladed weapons

import wolfpack
import random
import skills.lumberjacking
from wolfpack import utilities, tr, settings
from wolfpack.consts import *

# Lists of IDs
blood = [ "122a", "122b", "122d", "122f" ]
fish = [ 0x9cc, 0x9cd, 0x9ce, 0x9cf ]

def onUse( char, item ):
	char.socket.clilocmessage( 1010086 ) # What do you want to use this on?
	char.socket.attachtarget( "blades.response", [ item.serial ] )
	return 1

def regrow_wool(char, arguments):
	if char.npc:
		char.baseid = 'sheep_unsheered'
		char.id = 207
		char.update()

def response( char, args, target ):
	item = wolfpack.finditem( args[0] )
	if not item:
		return

	if target.char and not char.canreach(target.char, 5):
		char.socket.clilocmessage(500312) # You cannot reach that.
		return False

	elif not target.item and not char.canreach(target.pos, 5):
		char.socket.clilocmessage(500312) # You cannot reach that.
		return False

	docarve( char, item, target )
	return True

def carve_item( char, tool, target ):
	if target.item.id == 0x2006 and target.item.corpse:
		carve_corpse( char, tool, target.item )
		return True

	# For cutting fish
	elif target.item.id in fish:
		if target.item.getoutmostchar() != char:
			char.socket.clilocmessage(500312) # You cannot reach that.
			return True

		cut_fish(char, target.item)
		return True
	return False

def docarve( char, item, target ):
	# Corpse => Carve
	# Wood => Kindling/Logs
	model = 0

	if target.item:
		if carve_item( char, item, target ):
			return
		else:
			model = target.item.id

	# This is for sheering only
	elif target.char and target.char.npc:
		if target.char.baseid == 'sheep_unsheered':
			target.char.id = 223
			target.char.baseid = 'sheep_sheered'
			target.char.update()

			# Create Wool
			wool = wolfpack.additem("df8")
			wool.amount = 2

			if not utilities.tobackpack(wool, char):
				wool.update()

			# Resend weight
			char.socket.resendstatus()

			char.socket.clilocmessage( 500452 ) # You place the gathered wool into your backpack.

			# Let the wool regrow (minutes)
			delay = settings.getnumber('Game Speed', 'Regrow Wool Minutes', 180, 1)
			delay *= 60000 # Miliseconds per Minute
			target.char.dispel(None, 1, "regrow_wool", [])
			target.char.addtimer(delay, regrow_wool, [], 1, 0, "regrow_wool")
			return
		elif target.char.baseid == 'sheep' or target.char.baseid == 'sheep_sheered':
			char.socket.clilocmessage( 500449 ) # This sheep is not yet ready to be shorn.
			return
		else:
			char.socket.clilocmessage( 500450 ) # You can only skin dead creatures.
			return
	else:
		model = target.model

	if target.model == 0:
		map = wolfpack.map( target.pos.x, target.pos.y, target.pos.map )
		treeid = map['id']
	elif target.model != 0:
		treeid = target.model

	if utilities.istree(treeid):
		# Axes/Polearms get Logs, Swords get kindling.
		# Also allows a mace's war axe to be use. 0x13af and 0x13b0
		if item.type == 1002 or item.id == 0x13af or item.id == 0x13b0:
			if not item or not item.container == char:
				char.message( 502641, "" ) # You must equip this item to use it.
				return
			else:
				skills.lumberjacking.response( [ target, item, char ] )
		# Swords and Fencing Weapons: Get kindling
		elif item.type == 1001 or item.type == 1005:
			skills.lumberjacking.hack_kindling( char, target.pos )
	else:
		char.socket.clilocmessage( 500494, "", GRAY ) # You can't use a bladed item on that.
		return False

# CARVE CORPSE
def carve_corpse( char, tool, corpse ):
	if corpse.container:
		char.socket.sysmessage( tr("You can't carve corpses in a container") )
		return

	if not char.canreach(corpse, 3):
		char.socket.clilocmessage( 500312, "", 0x3b2, 3, corpse ) # You cannot reach that
		return

	# Human Bodies can always be carved
	if corpse.bodyid in PLAYER_BODIES_ALIVE:
		if corpse.hastag('carved') or not corpse.owner:
			char.socket.clilocmessage(500485) # You see nothing useful to carve from the corpse.
		else:	
			ITEMS = ['1d9f', '1da4', '1da2', '1da3', '1da1'] # Components of the carved body
			for item in ITEMS:
				item = wolfpack.additem(item)
				item.moveto(corpse.pos)
				item.decay = True # Make sure they decay
				item.movable = 1 # Make sure they are movable
				item.update()

			# Blood should not be movable
			blooditem = wolfpack.additem('122d')
			blooditem.moveto(corpse.pos)
			blooditem.decay = True
			blooditem.movable = 3
			blooditem.update()

			# Add the head
			head = wolfpack.additem('1da0')
			head.moveto(corpse.pos)
			head.decay = True
			head.movable = 3
			head.name = tr("the head of %s") % (corpse.owner.orgname)
			head.update()

			# Turn the corpse into a pile of bones
			corpse.removefromview()
			corpse.movable = 3 # The corpse is not movable
			corpse.id = random.randrange(0xeca, 0xed3)
			corpse.color = 0
			corpse.update()
		return

	# Not carvable or already carved
	if corpse.hastag('carved'):
		char.socket.clilocmessage( 500485, "", 0x3b2, 3, corpse ) # You see nothing useful to carve..
		return

	basedef = wolfpack.charbase(corpse.charbaseid)

	if not basedef:
		char.socket.clilocmessage( 500485, "", 0x3b2, 3, corpse ) # You see nothing useful to carve..
		return

	feathers = basedef.getintproperty('carve_feathers', 0)
	wool = basedef.getintproperty('carve_wool', 0)
	hides = basedef.getintproperty('carve_hides', 0)
	hides_type = basedef.getstrproperty('carve_hides_type', 'leather')
	scales = basedef.getintproperty('carve_scales', 0)
	scales_type = basedef.getstrproperty('carve_scales_type', 'red')
	meat = basedef.getintproperty('carve_meat', 0)
	meat_type = basedef.getstrproperty('carve_meat_type', 'ribs')

	if feathers == 0 and wool == 0 and hides == 0 and scales == 0 and meat == 0:
		char.socket.clilocmessage( 500485, "", 0x3b2, 3, corpse ) # You see nothing useful to carve..
		return

	# See if the corpse has blood
	bloodcolor = basedef.getintproperty('bloodcolor', 0)

	if bloodcolor != -1:
		try:
			if basedef.hasstrproperty('bloodcolor'):
				(minv, maxv) = basedef.getstrproperty('bloodcolor', '0,0').split(',')
				bloodcolor = random.randint(int(minv), int(maxv))
		except:
			pass

		# Create Random Blood
		bloodid = random.choice( blood )
		blooditem = wolfpack.additem( bloodid )
		blooditem.color = bloodcolor
		blooditem.decay = True
		blooditem.moveto( corpse.pos )
		blooditem.update()

	# Mark the corpse as carved
	corpse.settag('carved', 1)

	# Feathers
	if feathers != 0:
		carve_feathers( char, corpse, tool, feathers )

	# Wool
	if wool != 0:
		carve_wool( char, corpse, tool, wool )

	# Meat
	if meat != 0:
		carve_meat( char, corpse, tool, meat_type, meat )

	# Hides
	if hides != 0:
		carve_hides( char, corpse, tool, hides_type, hides )

	# Scales
	if scales != 0:
		carve_scales( char, corpse, tool, scales_type, scales )


def carve_feathers( char, corpse, tool, feathers ):
	item = wolfpack.additem('1bd1')
	item.amount = feathers
	if not wolfpack.utilities.tocontainer(item, corpse):
		item.update()
	char.socket.clilocmessage( 500479, "", 0x3b2, 3 ) # You pluck the bird. The feathers are now on the corpse.

def carve_wool( char, corpse, tool, wool ):
	item = wolfpack.additem('df8')
	item.amount = wool
	if not wolfpack.utilities.tocontainer(item, corpse):
		item.update()
	char.socket.clilocmessage( 500483, "", 0x3b2, 3 ) # You shear it, and the wool is now on the corpse.

def carve_meat( char, corpse, tool, meat_type, meat ):
	if meat_type == 'bird':			
		item = wolfpack.additem('9b9') # Raw Bird
	elif meat_type == 'lambleg':
		item = wolfpack.additem('1609') # Raw Lamb Leg
	elif meat_type == 'fishsteak':
		item = wolfpack.additem('97a') # Raw Fish Steak
	else:		
		item = wolfpack.additem('9f1') # Raw Ribs

	item.amount = meat
	if not wolfpack.utilities.tocontainer(item, corpse):
		item.update()
	char.socket.clilocmessage( 500467, "", 0x3b2, 3 ) # You carve some meat, which remains on the corpse.

def carve_hides( char, corpse, tool, hides_type, hides ):
	if hides_type == 'spined':
		item = wolfpack.additem('spined_leather_hides')
	elif hides_type == 'horned':
		item = wolfpack.additem('horned_leather_hides')
	elif hides_type == 'barbed':
		item = wolfpack.additem('barbed_leather_hides')
	else:
		item = wolfpack.additem('leather_hides')

	item.amount = hides
	if not wolfpack.utilities.tocontainer(item, corpse):
		item.update()
	char.socket.clilocmessage( 500471, "", 0x3b2, 3 ) # You skin it, and the hides are now in the corpse.

def carve_scales( char, corpse, tool, scales_type, scales ):
	# Random scales type
	if ',' in scales_type:
		scales_type = random.choice(scales_type.split(','))

	items = []
	if scales_type in ['blue', 'all']:
		items.append(wolfpack.additem('blue_scales'))
	if scales_type in ['green', 'all']:
		items.append(wolfpack.additem('green_scales'))
	if scales_type in ['yellow', 'all']:
		items.append(wolfpack.additem('yellow_scales'))
	if scales_type in ['black', 'all']:
		items.append(wolfpack.additem('black_scales'))
	if scales_type in ['white', 'all']:
		items.append(wolfpack.additem('white_scales'))
	if scales_type in ['red', 'all']:
		items.append(wolfpack.additem('red_scales'))
	for item in items:
		item.amount = scales
		if not wolfpack.utilities.tocontainer(item, corpse):
			item.update()
	char.socket.sysmessage( tr("You cut away some scales, but they remain on the corpse.") )

# CUT FISH
def cut_fish( char, item ):
	item_new = wolfpack.additem( "97a" )
	if item.baseid == "big_fish":
		item_new.amount = random.randint(16, item.gettag('animalweight')/4)
	else:
		item_new.amount = item.amount * 2
	if not utilities.tocontainer( item_new, char.getbackpack() ):
		item_new.update()
	item.delete()
