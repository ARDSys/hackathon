from hackathon.modules.TournamentMatrixCompareModule import TournamentMatrixCompareModule
from hackathon.modules.TournamentModule import SwissTournamentModule
from ard.subgraph import Subgraph
from hackathon.modules.generators.SkibidiGenerator import SkibidiGenerator
import json

subgraph = Subgraph.load_from_file("data/Bridge_Therapy.json")
with open("dzejson.json", 'r', encoding='UTF-8') as f:
    subgraph_json = json.load(f)
generator = SkibidiGenerator("small")
hypothesis = generator.run(subgraph, subgraph_json, num_hypothesis=2, max_workers=16)
cmp = TournamentMatrixCompareModule(subgraph, subgraph_json, "fast")
links = []
for i in range(len(hypothesis)):
    for j in range(i + 1, len(hypothesis)):
        links.append((i, j))
print(cmp(hypothesis, links))

# cmp = TournamentMatrixCompareModule("fast")
# hypothesis = [
#         "Alterations in gut microbiome composition contribute to the pathogenesis and flare frequency of seronegative spondyloarthropathies via modulation of mucosal immune responses.", 
#         "Chronic stress-induced dysregulation of the hypothalamic-pituitary-adrenal (HPA) axis contributes to increased disease activity and pain perception in patients with rheumatoid arthritis (RA) through altered glucocorticoid sensitivity.",
#         "blah blah blah skibidi sigmaaaaaa",
#         "Chronic low-level exposure to urban air pollutants, particularly nitrogen dioxide (NO₂) and fine particulate matter (PM2.5), increases the risk of developing rheumatoid arthritis by promoting citrullination of proteins in the lungs.",
#         "Alterations in the gut microbiome composition contribute to the onset and severity of rheumatoid arthritis (RA) through modulation of systemic immune responses and local joint inflammation.",
#         "In early-stage rheumatoid arthritis (RA), overrepresentation of Prevotella copri in the gut microbiome promotes Th17 cell differentiation via increased intestinal IL-6 and IL-23 expression, contributing to systemic inflammation and synovial joint infiltration by autoreactive T cells."
#     ]
# tournament = SwissTournamentModule(cmp)
# print(tournament(hypothesis))
