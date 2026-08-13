import re
import logging
import ontoweaver

logger = logging.getLogger("ontoweaver")

def check(names, target):
    rows = [{"name":name} for name in names]
    vm = ontoweaver.transformer.western_name.ValueMaker()
    for i,row in enumerate(rows):
        logger.info(f"────────────────────────────────────────────────")
        logger.info(f"Test {i}: check `{row['name']}`")
        found_name = None
        for found_name in vm(["name"], row, i):
            logger.info(f"Extracted: `{found_name}`")
            logger.info(f"Match against: '{target}'")
            matches = re.match(target, found_name)
            assert matches, f"Failed to match `{found_name}` in `{target}`"
        assert found_name, f"Failed to extract `{target}` from `{row['name']}`"


def test_name_dreo():
    names = [
        "Johann DREO",
        "Johann\tDREO",
        "Johann DREO",
        "Johann DRÉO",
        " Johann  DREO ",
        "DREO Johann",
        "DRÉO Johann",
        "Dreo, Johann",
        "Dréo,  Johann",
        "Johann Dreo",
        "Johann Dréo",
        "Johann Yves DREO",
        "Johann Yves DRÉO",
        "DREO Johann Yves",
        "DRÉO Johann Yves",
        "Johann Yves Dreo",
        "Johann Yves Dréo",
        "DREO Johann Y.",
        "DRÉO Johann Y.",
        "Johann Y. Dreo",
        "Johann Y. Dréo",
        "Johann Y. DREO",
        "Johann Y. DRÉO",
    ]
    check(names, r"^Dr[eé]o, Johann(\s+Y)*")


def test_name_initials():

    names = [
        "John R. R. Tolkien",
        "John R. R. TOLKIEN",
        "TOLKIEN John R. R.",
        "Tolkien John R. R.",
        "TOLKIEN, John R. R.",
        "Tolkien, John R. R.",
    ]
    check(names, r'Tolkien, John R. R.')

    names = [
        "J. M. G. Le Clézio",
        "J. M. G. LE CLÉZIO",
        "Le Clézio, J. M. G. ",
        "LE CLÉZIO J. M. G.",
    ]
    check(names, r'Le Clézio, J. M. G.')

    names = [
        "J. Robert Oppenheimer",
    ]
    check(names, r'Oppenheimer, J. Robert')

    names = [
        "J. Hans D. Jensen",
        "J. Hans D. JENSEN",
        "Jensen J. Hans D.",
        "JENSEN J. Hans D.",
    ]
    check(names, r'Jensen, J. Hans D.')

    names = [
        "E. O. Wilson",
    ]
    check(names, r'Wilson, E. O.')

    names = [
        "J. J. Thomson",
    ]
    check(names, r'Thomson, J. J.')

    names = [
        "Kip S. Thorne",
    ]
    check(names, r'Thorne, Kip S.')


def test_name_particles():
    names = [
        "Ernst Werner von Siemens",
        # "VON SIEMENS, Ernst Werner",  # Decapitalization not supported
        "von Siemens, Ernst Werner",
    ]
    check(names, r'von Siemens, Ernst Werner')

    names = [
        "Charles-Augustin de Coulomb",
    ]
    check(names, r'de Coulomb, Charles-Augustin')

    names = [
        "John von Neumann",
    ]
    check(names, r'von Neumann, John')


    names = [
        "Ramón y Cajal, Santiago",
        # "Santiago Ramón y Cajal", # Ambiguous, not supported, in favor of a heuristic favoring first names.
    ]
    check(names, r'Ramón y Cajal, Santiago')

    names = [
        "Balluet d'Estournelles de Constant de Rebecque, Paul Henri Benjamin ",
    ]
    check(names, r"Balluet d'Estournelles de Constant de Rebecque, Paul Henri Benjamin")


def test_name_classical():
    names = [
        "Joseph-Louis Lagrange",
    ]
    check(names, r'Lagrange, Joseph-Louis')

    names = [
        "Timothy John Berners-Lee",
    ]
    check(names, r'Berners-Lee, Timothy John')

    names = [
        "Jane Goodall",
    ]
    check(names, r'Goodall, Jane')

    names = [
        "Cecilia Payne-Gaposchkin",
    ]
    check(names, r'Payne-Gaposchkin, Cecilia')

    names = [
        "Thompson, DʼArcy Wentworth",
    ]
    check(names, r"Thompson, DʼArcy Wentworth")

    names = [
        "Anne L'Huillier",
        "Anne L'HUILLIER",
        "L'HUILLIER Anne",
        "L'Huillier, Anne",
    ]
    check(names, r"L'Huillier, Anne")


def test_name_multi_particles():

    names = [
        "Muhammad ibn Musa al-Khwarizmi",
        "ibn Musa al-Khwarizmi, Muhammad",
    ]
    check(names, r'ibn Musa al-Khwarizmi, Muhammad')

    names = [
        "Don Diego de la Vega",
    ]
    check(names, r'de la Vega, Don Diego')

    names = [
        "Don Diego de la Vega d'el Pueblo de Nuestra Señora la Reina de los Ángeles del Río de Porciúncula",
    ]
    check(names, r"de la Vega d'el Pueblo de Nuestra Señora la Reina de los Ángeles del Río de Porciúncula, Don Diego")

    names = [
        "Théodore Agrippa d'Aubigné",
    ]
    check(names, r"d'Aubigné, Théodore Agrippa")


def test_name_junior():
    names = [
        "Thomas Midgeley Jr.",
        "Thomas MIDGELEY JR.",
        "Thomas MIDGELEY Jr.",
        "Thomas Jr. Midgeley",
        "Thomas Jr. MIDGELEY",
        "Midgeley, Thomas Jr.",
        "MIDGELEY, Thomas Jr.",
        "MIDGELEY Thomas Jr.",
        "MIDGELEY Jr. Thomas",
        # "Midgeley Jr., Thomas",  # FIXME
    ]
    check(names, r'Midgeley, Thomas J[rR]\.')

    names = [
        "Thomas Midgeley Junior",
        "Thomas MIDGELEY Junior",
        "Thomas Junior Midgeley",
        "Thomas Junior MIDGELEY",
        "Midgeley, Thomas Junior",
        "MIDGELEY, Thomas Junior",
        "MIDGELEY Thomas Junior",
        "MIDGELEY Junior Thomas",
        # "Midgeley Junior, Thomas",  # FIXME
    ]
    check(names, r'Midgeley, Thomas Junior')

    names = [
        "Don Diego de la Vega Junior",
    ]
    check(names, r'de la Vega, Don Diego Junior')

    names = [
        "T-Rex Juniorus",
    ]
    check(names, r'Juniorus, T-Rex')

    # Test all registered retronyms.
    vm = ontoweaver.transformer.western_name.ValueMaker()
    for retronym in vm.retronyms:
        r = retronym.replace('\\','')
        n = r.replace('.','').capitalize()
        check([f"T-Rex {n}us {r}"], f"{n}us, T-Rex {r}")


if __name__ == "__main__":
    test_name_classical()
    test_name_dreo()
    test_name_initials()
    test_name_particles()
    test_name_junior()
