import requests

class EnsemblApiClient:
    """
    A client for interacting with the Ensembl REST API.

    Attributes:
        base_url (str): The base URL for the Ensembl REST API.
        headers (dict): The headers used for API requests.
    """

    def __init__(self, base_url="https://rest.ensembl.org"):
        """
        Initializes the EnsemblApiClient with a base URL and default headers.

        Args:
            base_url (str): The base URL for the Ensembl REST API (default is "https://rest.ensembl.org").
        """
        self.base_url = base_url
        self.headers = {"Content-Type": "application/json", "Accept": "application/json"}

    def _make_request(self, method, endpoint, params=None, data=None):
        """
        Makes an HTTP request to the Ensembl REST API.

        Args:
            method (str): The HTTP method (e.g., "GET", "POST").
            endpoint (str): The API endpoint to call.
            params (dict, optional): Query parameters for the request (default is None).
            data (dict, optional): JSON data to send in the request body (default is None).

        Returns:
            dict: The JSON response from the API.

        Raises:
            Exception: If the API request fails with a non-200 status code.
        """
        url = f"{self.base_url}/{endpoint}"
        response = requests.request(method, url, headers=self.headers, params=params, json=data)

        if response.status_code != 200:
            raise Exception(f"Request failed [{response.status_code}]: {response.text}")
        return response.json()

    def get(self, endpoint, params=None):
        """
        Sends a GET request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to call.
            params (dict, optional): Query parameters for the request (default is None).

        Returns:
            dict: The JSON response from the API.
        """
        return self._make_request("GET", endpoint, params=params)

    def post(self, endpoint, data=None):
        """
        Sends a POST request to the specified API endpoint.

        Args:
            endpoint (str): The API endpoint to call.
            data (dict, optional): JSON data to send in the request body (default is None).

        Returns:
            dict: The JSON response from the API.
        """
        return self._make_request("POST", endpoint, data=data)

        # GENETREE-RELATED METHODS

    def get_cafe_genetree_by_id(self, gene_tree_id):
        """
        Retrieves a CAFE gene tree by its ID.

        Args:
            gene_tree_id (str): The ID of the CAFE gene tree.

        Returns:
            dict: The JSON response containing the CAFE gene tree data.
        """
        return self.get(f"cafe/genetree/id/{gene_tree_id}")

    def get_cafe_genetree_by_symbol(self, species, symbol):
        """
        Retrieves a CAFE gene tree by species and gene symbol.

        Args:
            species (str): The species name.
            symbol (str): The gene symbol.

        Returns:
            dict: The JSON response containing the CAFE gene tree data.
        """
        return self.get(f"cafe/genetree/member/symbol/{species}/{symbol}")

    def get_cafe_genetree_by_member_id(self, species, member_id):
        """
        Retrieves a CAFE gene tree by species and member ID.

        Args:
            species (str): The species name.
            member_id (str): The member ID.

        Returns:
            dict: The JSON response containing the CAFE gene tree data.
        """
        return self.get(f"cafe/genetree/member/id/{species}/{member_id}")

    def get_genetree_by_id(self, gene_tree_id):
        """
        Retrieves a gene tree by its ID.

        Args:
            gene_tree_id (str): The ID of the gene tree.

        Returns:
            dict: The JSON response containing the gene tree data.
        """
        return self.get(f"genetree/id/{gene_tree_id}")

    def get_genetree_by_symbol(self, species, symbol):
        """
        Retrieves a gene tree by species and gene symbol.

        Args:
            species (str): The species name.
            symbol (str): The gene symbol.

        Returns:
            dict: The JSON response containing the gene tree data.
        """
        return self.get(f"genetree/member/symbol/{species}/{symbol}")

    def get_genetree_by_member_id(self, species, member_id):
        """
        Retrieves a gene tree by species and member ID.

        Args:
            species (str): The species name.
            member_id (str): The member ID.

        Returns:
            dict: The JSON response containing the gene tree data.
        """
        return self.get(f"genetree/member/id/{species}/{member_id}")

  # CROSS REFERENCES

    def get_xrefs_by_symbol(self, species, symbol):
        """
        Retrieves all Ensembl objects linked to an external symbol.

        Args:
            species (str): The species name.
            symbol (str): The external symbol to look up.

        Returns:
            dict: The JSON response containing the linked Ensembl objects.
        """
        return self.get(f"xrefs/symbol/{species}/{symbol}")

    def get_xrefs_by_id(self, ensembl_id):
        """
        Retrieves external references linked to a specific Ensembl ID.

        Args:
            ensembl_id (str): The Ensembl ID to look up.

        Returns:
            dict: The JSON response containing the external references.
        """
        return self.get(f"xrefs/id/{ensembl_id}")

    def get_xrefs_by_name(self, species, name):
        """
        Retrieves Ensembl objects linked to a primary accession or display label.

        Args:
            species (str): The species name.
            name (str): The primary accession or display label to look up.

        Returns:
            dict: The JSON response containing the linked Ensembl objects.
        """
        return self.get(f"xrefs/name/{species}/{name}")

    # INFORMATION - Sequence-Related

    def get_assembly_info(self, species):
        """
        Retrieves assembly information for a specific species.

        Args:
            species (str): The species name.

        Returns:
            dict: The JSON response containing the assembly information.
        """
        return self.get(f"info/assembly/{species}")

    def get_region_info(self, species, region_name):
        """
        Retrieves information about a specific region of a species' genome.

        Args:
            species (str): The species name.
            region_name (str): The name of the region to look up.

        Returns:
            dict: The JSON response containing the region information.
        """
        return self.get(f"info/assembly/{species}/{region_name}")

    def get_biotypes(self, species):
        """
        Retrieves all biotypes available for a specific species.

        Args:
            species (str): The species name.

        Returns:
            dict: The JSON response containing the biotypes.
        """
        return self.get(f"info/biotypes/{species}")

    def get_biotype_by_name(self, name, object_type):
        """
        Retrieves information about a specific biotype by name and object type.

        Args:
            name (str): The name of the biotype.
            object_type (str): The type of object (e.g., gene, transcript).

        Returns:
            dict: The JSON response containing the biotype information.
        """
        return self.get(f"info/biotypes/name/{name}/{object_type}")

    def get_species_list(self):
        """
        Retrieves a list of all species available in the Ensembl database.

        Returns:
            dict: The JSON response containing the list of species.
        """
        return self.get("info/species")

    def get_genome_info(self, genome_name):
        """
        Retrieves genome information for a specific genome.

        Args:
            genome_name (str): The name of the genome.

        Returns:
            dict: The JSON response containing the genome information.
        """
        return self.get(f"info/genomes/{genome_name}")

    def get_assembly_by_id(self, assembly_id):
        """
        Retrieves assembly information for a specific assembly ID.

        Args:
            assembly_id (str): The ID of the assembly.

        Returns:
            dict: The JSON response containing the assembly information.
        """
        return self.get(f"info/genomes/assembly/{assembly_id}")

    def get_assembly_info(self, species):
        """
        Retrieves assembly information for a specific species.

        Args:
            species (str): The species name.

        Returns:
            dict: The JSON response containing the assembly information.
        """
        return self.get(f"info/assembly/{species}")

    def get_region_info(self, species, region_name):
        """
        Retrieves information about a specific region of a species' genome.

        Args:
            species (str): The species name.
            region_name (str): The name of the region to look up.

        Returns:
            dict: The JSON response containing the region information.
        """
        return self.get(f"info/assembly/{species}/{region_name}")

    def get_biotypes(self, species):
        """
        Retrieves all biotypes available for a specific species.

        Args:
            species (str): The species name.

        Returns:
            dict: The JSON response containing the biotypes.
        """
        return self.get(f"info/biotypes/{species}")

    def get_biotype_by_name(self, name, object_type):
        """
        Retrieves information about a specific biotype by name and object type.

        Args:
            name (str): The name of the biotype.
            object_type (str): The type of object (e.g., gene, transcript).

        Returns:
            dict: The JSON response containing the biotype information.
        """
        return self.get(f"info/biotypes/name/{name}/{object_type}")

    def get_species_list(self):
        """
        Retrieves a list of all species available in the Ensembl database.

        Returns:
            dict: The JSON response containing the list of species.
        """
        return self.get("info/species")

    def get_genome_info(self, genome_name):
        """
        Retrieves genome information for a specific genome.

        Args:
            genome_name (str): The name of the genome.

        Returns:
            dict: The JSON response containing the genome information.
        """
        return self.get(f"info/genomes/{genome_name}")

    def get_assembly_by_id(self, assembly_id):
        """
        Retrieves assembly information for a specific assembly ID.

        Args:
            assembly_id (str): The ID of the assembly.

        Returns:
            dict: The JSON response containing the assembly information.
        """
        return self.get(f"info/genomes/assembly/{assembly_id}")

    # LOOKUP

    def get_lookup_by_id(self, identifier):
        """
        Finds species and database for a single identifier (e.g., gene, transcript).

        Args:
            identifier (str): The identifier to look up.

        Returns:
            dict: The JSON response containing species and database information.
        """
        return self.get(f"lookup/id/{identifier}")

    def post_lookup_by_ids(self, id_list):
        """
        Finds species and database for multiple identifiers.

        Args:
            id_list (list of str): A list of identifiers to look up.

        Returns:
            dict: The JSON response containing species and database information for the identifiers.
        """
        return self.post("lookup/id", data={"ids": id_list})

    def get_lookup_by_symbol(self, species, symbol):
        """
        Finds species and database for a symbol in an external database.

        Args:
            species (str): The species name.
            symbol (str): The symbol to look up.

        Returns:
            dict: The JSON response containing species and database information for the symbol.
        """
        return self.get(f"lookup/symbol/{species}/{symbol}")

    def post_lookup_by_symbols(self, species, symbols):
        """
        Finds species and database for a list of symbols.

        Args:
            species (str): The species name.
            symbols (list of str): A list of symbols to look up.

        Returns:
            dict: The JSON response containing species and database information for the symbols.
        """
        return self.post(f"lookup/symbol/{species}", data={"symbols": symbols})

    # OVERLAP

    def get_overlap_by_id(self, feature_id):
        """
        Retrieves overlap information for a specific feature ID.

        Args:
            feature_id (str): The ID of the feature to retrieve overlap information for.

        Returns:
            dict: The JSON response containing the overlap information.
        """
        return self.get(f"overlap/id/{feature_id}")

    def get_overlap_by_region(self, species, region):
        """
        Retrieves overlap information for a specific region in a species' genome.

        Args:
            species (str): The species name.
            region (str): The genomic region to retrieve overlap information for.

        Returns:
            dict: The JSON response containing the overlap information.
        """
        return self.get(f"overlap/region/{species}/{region}")

    def get_overlap_by_translation(self, translation_id):
        """
        Retrieves overlap information for a specific translation ID.

        Args:
            translation_id (str): The ID of the translation to retrieve overlap information for.

        Returns:
            dict: The JSON response containing the overlap information.
        """
        return self.get(f"overlap/translation/{translation_id}")

    # PHENOTYPE ANNOTATIONS

    def get_phenotype_by_accession(self, species, accession):
        """
        Retrieves phenotype annotations for a specific accession in a species.

        Args:
            species (str): The species name.
            accession (str): The accession to retrieve phenotype annotations for.

        Returns:
            dict: The JSON response containing the phenotype annotations.
        """
        return self.get(f"phenotype/accession/{species}/{accession}")

    def get_phenotype_by_gene(self, species, gene_id):
        """
        Retrieves phenotype annotations for a specific gene in a species.

        Args:
            species (str): The species name.
            gene_id (str): The ID of the gene to retrieve phenotype annotations for.

        Returns:
            dict: The JSON response containing the phenotype annotations.
        """
        return self.get(f"phenotype/gene/{species}/{gene_id}")

    def get_phenotype_by_region(self, species, region):
        """
        Retrieves phenotype annotations for a specific region in a species' genome.

        Args:
            species (str): The species name.
            region (str): The genomic region to retrieve phenotype annotations for.

        Returns:
            dict: The JSON response containing the phenotype annotations.
        """
        return self.get(f"phenotype/region/{species}/{region}")

    def get_phenotype_by_term(self, species, term):
        """
        Retrieves phenotype annotations for a specific term in a species.

        Args:
            species (str): The species name.
            term (str): The term to retrieve phenotype annotations for.

        Returns:
            dict: The JSON response containing the phenotype annotations.
        """
        return self.get(f"phenotype/term/{species}/{term}")

    # SEQUENCE

    def get_sequence_by_id(self, stable_id):
        """
        Retrieves the sequence for a specific stable ID.

        Args:
            stable_id (str): The stable ID of the sequence to retrieve.

        Returns:
            dict: The JSON response containing the sequence data.
        """
        return self.get(f"sequence/id/{stable_id}")

    def post_sequence_by_ids(self, ids):
        """
        Retrieves sequences for multiple stable IDs.

        Args:
            ids (list of str): A list of stable IDs to retrieve sequences for.

        Returns:
            dict: The JSON response containing the sequences data.
        """
        return self.post("sequence/id", data={"ids": ids})

    def get_sequence_by_region(self, species, region):
        """
        Retrieves the sequence for a specific genomic region in a species.

        Args:
            species (str): The species name.
            region (str): The genomic region to retrieve the sequence for.

        Returns:
            dict: The JSON response containing the sequence data.
        """
        return self.get(f"sequence/region/{species}/{region}")

    def post_sequence_by_regions(self, species, regions):
        """
        Retrieves sequences for multiple genomic regions in a species.

        Args:
            species (str): The species name.
            regions (list of str): A list of genomic regions to retrieve sequences for.

        Returns:
            dict: The JSON response containing the sequences data.
        """
        return self.post(f"sequence/region/{species}", data={"regions": regions})

    # VEP

    def get_vep_by_id(self, species, variant_id):
        """
        Retrieves Variant Effect Predictor (VEP) results for a specific variant ID.

        Args:
            species (str): The species name.
            variant_id (str): The variant ID to retrieve VEP results for.

        Returns:
            dict: The JSON response containing the VEP results.
        """
        return self.get(f"vep/{species}/id/{variant_id}")

    def post_vep_by_ids(self, species, ids):
        """
        Retrieves VEP results for multiple variant IDs.

        Args:
            species (str): The species name.
            ids (list of str): A list of variant IDs to retrieve VEP results for.

        Returns:
            dict: The JSON response containing the VEP results.
        """
        return self.post(f"vep/{species}/id", data={"ids": ids})

    # VARIATION

    def get_variant_recoder(self, species, variant_id):
        """
        Translates a variant identifier or notation to all equivalent forms (e.g., HGVS, SPDI).

        Args:
            species (str): The species name.
            variant_id (str): The variant ID or notation to translate.

        Returns:
            dict: The JSON response containing the equivalent forms of the variant.
        """
        return self.get(f"variant_recoder/{species}/{variant_id}")

    def post_variant_recoder(self, species, identifiers):
        """
        Translates a list of variant identifiers or notations to all equivalent forms.

        Args:
            species (str): The species name.
            identifiers (list of str): A list of variant IDs or notations to translate.

        Returns:
            dict: The JSON response containing the equivalent forms of the variants.
        """
        return self.post(f"variant_recoder/{species}", data={"ids": identifiers})

    def get_variation_by_id(self, species, variant_id):
        """
        Fetches variation features by Ensembl ID (e.g., rsID).

        Args:
            species (str): The species name.
            variant_id (str): The Ensembl ID of the variation to retrieve.

        Returns:
            dict: The JSON response containing the variation features.
        """
        return self.get(f"variation/{species}/{variant_id}")

    def get_variation_by_pmcid(self, species, pmcid):
        """
        Fetches variants associated with a specific publication (PubMed Central ID).

        Args:
            species (str): The species name.
            pmcid (str): The PubMed Central ID of the publication.

        Returns:
            dict: The JSON response containing the associated variants.
        """
        return self.get(f"variation/{species}/pmcid/{pmcid}")

    def get_variation_by_pmid(self, species, pmid):
        """
        Fetches variants associated with a specific publication (PubMed ID).

        Args:
            species (str): The species name.
            pmid (str): The PubMed ID of the publication.

        Returns:
            dict: The JSON response containing the associated variants.
        """
        return self.get(f"variation/{species}/pmid/{pmid}")

    def post_variations_by_ids(self, species, ids):
        """
        Fetches variation features for a list of variant IDs (e.g., rsIDs).

        Args:
            species (str): The species name.
            ids (list of str): A list of variant IDs to retrieve variation features for.

        Returns:
            dict: The JSON response containing the variation features.
        """
        return self.post(f"variation/{species}", data={"ids": ids})



# Usage example:
if __name__ == "__main__":
    client = EnsemblApiClient()
    post_variation = client.get_variation_by_pmcid("human", "PMC5002951")
    result2  = client.get_phenotype_by_term("human", "neurodevelopmental disorder")
    print(post_variation)