from gedcom.element.individual import IndividualElement
from gedcom.parser import Parser
from gedcom.parser import FAMILY_MEMBERS_TYPE_CHILDREN
import re

# Path to your `.ged` file
#file_path = 'bigged.ged'
#file_path = '100gen.ged'
#file_path = 'wayback.ged'
#file_path = 'descendents.ged'
#file_path = 'descendents2.ged'
#file_path = 'ancestralquest.ged'
#file_path = 'descendents3.ged'
file_path = 'descendents4.ged'

# Initialize the parser
gedcom_parser = Parser()

print ("Parsing...")
# Parse your file
gedcom_parser.parse_file(file_path)

## Support methods
def print_name(person):
    (first, last) = person.get_name()
    death_year = person.get_death_year()
    birth_year = person.get_birth_year()
    name = "{} /{}/({})".format(first,last,birth_year)
    child_elems = person.get_child_elements()
    fsftid = ""
    for elem in child_elems:
        if (elem.get_tag() == '_FSFTID'):
            fsftid = elem.get_value()
            break
    ged = person.to_gedcom_string(True)
    return name+"["+fsftid+"]"

# compare routes to person
def compare_route(route1,route2):
    route1_list = route1.split("->")
    route2_list = route2.split("->")
    same_start = []
    same_end = []
    while (len(route1_list) and len(route2_list)):
        if (route1_list[0] == route2_list[0]):
            p1 = route1_list.pop(0)
            route2_list.pop(0)
            same_start.append(p1)
        else:
            break
    while (len(route1_list) and len(route2_list)):
        if (route1_list[-1] == route2_list[-1]):
            p1 = route1_list.pop()
            route2_list.pop()
            same_end.insert(0,p1)
        else:
            break
    start_length =len(same_start)
    end_length = len(same_end)
    firstgen = len(route1_list)
    secondgen = len(route2_list)
    print ("{} generations -> {}/{} -> {}\n{}\n  1.{}\n  2.{}\n{}\n".format(start_length,firstgen,secondgen,end_length,"->".join(same_start),"->".join(route1_list),"->".join(route2_list),"->".join(same_end)))


print ("finding root...")
root_child_elements = gedcom_parser.get_root_child_elements()

me = None
# Iterate through all root child elements
for element in root_child_elements:

    # Is the `element` an actual `IndividualElement`? (Allows usage of extra functions such as `surname_match` and `get_name`.)
    if isinstance(element, IndividualElement):
        if not me:
            me = element





# Show parents by generation


seen_parents = set()
seen_parents_route = {}
def parent_finder(person, route=""):
    parents = gedcom_parser.get_parents(person)
    for parent in parents:
        if (parent in seen_parents):
            if (seen_parents_route[parent] != route):
                #print ("Duplicate : {}\n{}\n{}\n".format(print_name(parent),seen_parents_route[parent],route))
                compare_route(seen_parents_route[parent],route)
        else:
            seen_parents.add(parent)
            seen_parents_route[parent] = route
            parent_finder(parent, route+"->"+print_name(person))

print("finding parents")


parent_finder(me)


oldest_generation = set()
oldest_generation_number = {}
seen = set()

def get_generation(people,generation):
    next_gen = []
    next_gen_set = set()
    while people:
        person = people.pop()
        seen.add(person)
        parents = gedcom_parser.get_parents(person)
        next_gen += parents
        next_gen_set.update(parents)
        if not len(parents):
            oldest_generation.add(person)
            (first, last) = person.get_name()
            #print ("@@ oldest: {} /{}/ generation : {}".format(first,last,generation))
            if (person not in oldest_generation_number):
                oldest_generation_number[person] = []
            oldest_generation_number[person] += [generation]
            #print ("@@ oldest: {} /{}/ generation : {}, num: {}".format(first,last,generation, oldest_generation_number[person]))
    not_seen = next_gen_set.difference(seen)
    dups = next_gen_set.intersection(seen)
    print ("{} generation: members: {}, parents: {}, unique_parents: {}, not_seen: {}, dups: {},  expected: {}".format(generation, len(people), len(next_gen), len(next_gen_set), len(not_seen), len(dups), 2**generation))
    if (len(dups) > 0):
        print(set(map(print_name,dups)))
    if (len(next_gen) > 0):
        get_generation(not_seen, generation+1)


# as artifact, get the oldest endpoints
get_generation([me],1)


relatives = set()
relatives_route = {}
families_set = set()

def get_unique_descendents(person,route=""):
    name = print_name(person)
    new_route = route + "->"+name
    #print (new_route)
    families = gedcom_parser.get_families(person)
    for family in families:
        # go over each family only once
        if (family in families_set):
            continue
        else:
            families_set.add(family)
            children = gedcom_parser.get_family_members(family,FAMILY_MEMBERS_TYPE_CHILDREN)
            for child in children:
                if (not child in seen):
                    new_person = new_route+"->"+print_name(child)
                    if (child in relatives):
                        # Seems odd that we end up with the same complete route
                        # Would think that since we only do a family once, it should not happen
                        old_person = relatives_route[child]
                        if (new_person != old_person): 
                            #print ("Repeat: {}\n------: {}".format(new_person,old_person))
                            compare_route(new_person,old_person)
                            print ("===================\n")
                    else:
                        relatives.add(child)
                        relatives_route[child] = new_person
                        get_unique_descendents(child,new_route)



def find_internal_relatives():
    print ("Finding internal relatives...")
    for person in oldest_generation:
        get_unique_descendents(person)


find_internal_relatives()

quit()


bygen = {}
def get_descendents(person, generation=0):
    (first, last) = person.get_name()
    death_year = person.get_death_year()
    birth_year = person.get_birth_year()
    print ("@#@ Getting for {} /{}/, born: {}, died: {}".format(first,last,birth_year,death_year))
    if (person in seen):
        print ("Seeing again: {} /{}/ : generation: {}".format(first, last, generation))
        return 0
    seen.add(person)
    families = gedcom_parser.get_families(person)
    if (len(families) > 1):
        print ("{} families: {} /{}/ - generation: {}, birth: {}, death: {}".format(len(families),first,last,generation, birth_year,death_year))
    count = 1
    if (not len(families)):
        if generation in bygen:
            bygen[generation]['kids'] = bygen[generation]['kids'] +1
            if (birth_year >0 and birth_year < bygen[generation]['min']):
                bygen[generation]['min'] = birth_year
            if (birth_year > bygen[generation]['max']):
                bygen[generation]['max'] = birth_year
        else:
            bygen[generation] = { 'kids': 1, 'min': birth_year, 'max': birth_year }
        return count
    for family in families:
        children = gedcom_parser.get_family_members(family,FAMILY_MEMBERS_TYPE_CHILDREN)
        if (not generation in bygen):
            bygen[generation] = {'kids': 0, 'min':9999, 'max': -1}
        for child in children:
            descendents = get_descendents(child,generation+1)
            if (descendents == 0):
                print (" -- no descendents: {} /{}/ : generation: {}".format(first, last, generation))
            bygen[generation]['kids'] = bygen[generation]['kids'] +1
            if (birth_year >100 and birth_year < bygen[generation]['min']):
                bygen[generation]['min'] = birth_year
            if (birth_year > bygen[generation]['max']):
                bygen[generation]['max'] = birth_year
            count += descendents
        #print ("[{}]".format(count))
    if (count > 2):
        (first, last) = person.get_name()
        birthyear = person.get_birth_year()
        #print("{} /{}/ generation: {}, birth year: {}, count: {}".format(first,last,generation,birthyear,count))
        
    return count



for person in oldest_generation:
    bygen.clear()
    seen.clear()
    #print(person.to_gedcom_string(True))
    print ("=======================")
    count = get_descendents(person)
    (first, last) = person.get_name()
    birthyear = person.get_birth_year()
    generations = oldest_generation_number[person]
    # Print the first and last name of the found individual
   
    age = -1
    if (birthyear > 0):
        age = 2022 - birthyear 
    print("%%{} /{}/ birth: {}, count: {}, generations: {}, age: {}, year/gen: {:.2f}, descs/gen: {:.2f}".format(first,last,birthyear,count,generations,age,age/generations[0],count/generations[0]))
    print(bygen)
    print("----------")


