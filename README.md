# The Local Graph

**Group 3's campus navigation solution**

**Project by:** Ashton Pankey, Chase Varvayanis, Dylan Henley, Marcel Ortiz, and Melanie Foley  
**Readme by:** Chase Varvayanis

Link to meeting notes for Joe: https://docs.google.com/document/d/1ubF6wsYMC7tI2S15a7-ESKGq623QfgO-6o0--jVlKSo/edit?usp=sharing

---

## To Run

- Open `RUN_LOCAL_GRAPH.py`  
  All dependencies should automatically be installed.

---

## Use Instructions

- **Navigation:**  
  Search for a start and end point by typing into the boxes below the map, then select **Find Route** at the bottom of the page to plot your route.
  
- **Intermediate Waypoints:**  
  If you would like to add intermediate waypoints (for example, going from Fir to Manzanita to Oak Pavilion), select **Fir** as the start waypoint and **Oak Pavilion** as the end waypoint. Under the **Optional Waypoints** heading, either search or use the dropdown box to add intermediate waypoints. Once all start, finish, and intermediate waypoints are added, select **Find Route** again at the bottom of the page.
  
- **Clearing the Path:**  
  To clear the path and start a new search query, select the **Clear Paths** button at the bottom of the page.
  
- **Viewing All Path Data:**  
  To see all path data in the system, select the **All Path Data** checkbox at the bottom of the page to toggle its visibility.

---

## Planned/Potential Future Features

- More comprehensive campus trail and building data.
- AI text-to-speech and voice navigation.
- Compilation into a standalone executable (Streamlit made this more challenging than anticipated).
- Hosting the application on a web server.

---

## Known Issues

- Certain paths have display errors (notably, the path between ~Pinyon and Ponderosa has a graphical display error).
- Path data is not comprehensive; some auxiliary and primary paths are missing from our dataset, including:
  - The path from dorm parking to campus.
  - Lower student parking by Oak Pavilion.
  - The path between Redbud and Tamarack Hall.
