"""
Module: STA2REST

Author: Filippo Finke

This module provides utility functions to convert various elements used in SensorThings queries to their corresponding
representations in a REST API.
"""
import re
import sta_parser.ast as ast
from .filter_visitor import FilterVisitor
from odata_query.grammar import ODataLexer
from odata_query.grammar import ODataParser
from sta_parser.lexer import Lexer
from sta_parser.visitor import Visitor
from sta_parser.parser import Parser

# Create the OData lexer and parser
odata_filter_lexer = ODataLexer()
odata_filter_parser = ODataParser()

class NodeVisitor(Visitor):
    """
    This class provides a visitor to convert a STA query to a PostgREST query.
    """
    
    def visit_IdentifierNode(self, node: ast.IdentifierNode):
        """
        Visit an identifier node.

        Args:
            node (ast.IdentifierNode): The identifier node to visit.

        Returns:
            str: The converted identifier.
        """
        return node.name

    def visit_SelectNode(self, node: ast.SelectNode):
        """
        Visit a select node.

        Args:
            node (ast.SelectNode): The select node to visit.

        Returns:
            str: The converted select node.
        """

        identifiers = ','.join([self.visit(identifier) for identifier in node.identifiers])
        return f'select={identifiers}'

    def visit_FilterNode(self, node: ast.FilterNode):
        """
        Visit a filter node.

        Args:
            node (ast.FilterNode): The filter node to visit.
        
        Returns:
            str: The converted filter node.
        """

        # Parse the filter using the OData lexer and parser
        ast = odata_filter_parser.parse(odata_filter_lexer.tokenize(node.filter))
        # Visit the tree to convert the filter
        res = FilterVisitor().visit(ast)
        return res

    def visit_OrderByNodeIdentifier(self, node: ast.OrderByNodeIdentifier):
        """
        Visit an orderby node identifier.

        Args:
            node (ast.OrderByNodeIdentifier): The orderby node identifier to visit.

        Returns:
            str: The converted orderby node identifier.
        """

        # Convert the identifier to the format name.order
        return f'{node.identifier}.{node.order}'

    def visit_OrderByNode(self, node: ast.OrderByNode):
        """
        Visit an orderby node.

        Args:
            node (ast.OrderByNode): The orderby node to visit.
        
        Returns:
            str: The converted orderby node.
        """
        identifiers = ','.join([self.visit(identifier) for identifier in node.identifiers])
        return f'order={identifiers}'

    def visit_SkipNode(self, node: ast.SkipNode):
        """
        Visit a skip node.

        Args:
            node (ast.SkipNode): The skip node to visit.
        
        Returns:
            str: The converted skip node.
        """
        return f'offset={node.count}'

    def visit_TopNode(self, node: ast.TopNode):
        """
        Visit a top node.

        Args:
            node (ast.TopNode): The top node to visit.
        
        Returns:
            str: The converted top node.
        """
        return f'limit={node.count}'

    def visit_CountNode(self, node: ast.CountNode):
        """
        Visit a count node.

        Args:
            node (ast.CountNode): The count node to visit.
        
        Returns:
            str: The converted count node.
        """
        return f'count={node.value}'
    
    def visit_ExpandNode(self, node: ast.ExpandNode, parent=None):
        """
        Visit an expand node.
        
        Args:
            node (ast.ExpandNode): The expand node to visit.
            parent (str): The parent entity name.
        
        Returns:
            dict: The converted expand node.
        """

        # dict to store the converted parts of the expand node
        select = None
        filter = ""
        orderby = ""
        skip = ""
        top = ""
        count = ""

        # Visit the identifiers in the expand node
        for expand_identifier in node.identifiers:
                # Convert the table name
                expand_identifier.identifier = STA2REST.convert_entity(expand_identifier.identifier)
                
                # Check if we had a parent entity
                prefix = ""
                if parent:
                    prefix = parent
                prefix += expand_identifier.identifier + "."
        
                # Check if we have a subquery
                if expand_identifier.subquery:

                    # check if we have a select, filter, orderby, skip, top or count in the subquery
                    if expand_identifier.subquery.select:
                        if not select:
                            select = ast.SelectNode([])
                        identifiers = ','.join([self.visit(identifier) for identifier in expand_identifier.subquery.select.identifiers])
                        select.identifiers.append(ast.IdentifierNode(f'{expand_identifier.identifier}({identifiers})'))
                    if expand_identifier.subquery.filter:
                        result = self.visit_FilterNode(expand_identifier.subquery.filter)
                        filter = prefix + result
                    if expand_identifier.subquery.orderby:
                        orderby = prefix + "order=" + ','.join([self.visit(identifier) for identifier in expand_identifier.subquery.orderby.identifiers])
                    if expand_identifier.subquery.skip:
                        skip = prefix + "offset=" + str(expand_identifier.subquery.skip.count)
                    if expand_identifier.subquery.top:
                        top = prefix + "limit=" + str(expand_identifier.subquery.top.count)
                    if expand_identifier.subquery.count:
                        count = prefix + "count=" + str(expand_identifier.subquery.count.value).lower()

                    # check if we have a subquery in the subquery
                    if expand_identifier.subquery.expand:
                        result = self.visit_ExpandNode(expand_identifier.subquery.expand, prefix)

                        # merge the results
                        if result['select']:
                            if not select:
                                select = ast.SelectNode([])
                            select.identifiers.extend(result['select'].identifiers)
                        if result['orderby']:
                            if orderby:
                                orderby += "&"
                            orderby += result['orderby']
                        if result['skip']:
                            if skip:
                                skip += "&"
                            skip += result['skip']
                        if result['top']:
                            if top:
                                top += "&"
                            top += result['top']
                        if result['count']:
                            if count:
                                count += "&"
                            count += result['count']
                        if result['filter']:
                            if filter:
                                filter += "&"
                            filter += result['filter']
                
                # If we don't have a subquery, we add the identifier to the select node
                if not expand_identifier.subquery or not expand_identifier.subquery.select:
                    if not select:
                        select = ast.SelectNode([])
                    select.identifiers.append(ast.IdentifierNode(f'{expand_identifier.identifier}(*)'))
        
        # Return the converted expand node
        return {
            'select': select,
            'filter': filter,
            'orderby': orderby,
            'skip': skip,
            'top': top,
            'count': count
        }

    def visit_QueryNode(self, node: ast.QueryNode):
        """
        Visit a query node.

        Args:
            node (ast.QueryNode): The query node to visit.
        
        Returns:
            str: The converted query node.
        """

        # list to store the converted parts of the query node
        query_parts = []

        # Check if we have an expand node before the other parts of the query
        if node.expand:
            # Visit the expand node
            result = self.visit(node.expand)

            # Merge the results with the other parts of the query
            if result['select']:
                if not node.select:
                    node.select = ast.SelectNode([])
                node.select.identifiers.extend(result['select'].identifiers)
            if result['orderby']:
                query_parts.append(result['orderby'])
            if result['skip']:
                query_parts.append(result['skip'])
            if result['top']:
                query_parts.append(result['top'])
            if result['count']:
                query_parts.append(result['count'])
            if result['filter']:
                query_parts.append(result['filter'])

        # Check if we have a select, filter, orderby, skip, top or count in the query
        if node.select:
            query_parts.append(self.visit(node.select))
        if node.filter:
            query_parts.append(self.visit(node.filter))
        if node.orderby:
            query_parts.append(self.visit(node.orderby))
        if node.skip:
            query_parts.append(self.visit(node.skip))
        if node.top:
            query_parts.append(self.visit(node.top))
        if node.count:
            query_parts.append(self.visit(node.count).lower())

        
        # Join the converted parts of the query
        return '&'.join(query_parts)

class STA2REST:
    """
    This class provides utility functions to convert various elements used in SensorThings queries to their corresponding
    representations in a REST API.
    """

    # Mapping from SensorThings entities to their corresponding database table names
    ENTITY_MAPPING = {
        "Things": "Thing",
        "Locations": "Location",
        "Sensors": "Sensor",
        "ObservedProperties": "ObservedProperty",
        "Datastreams": "Datastream",
        "Observations": "Observation",
        "FeaturesOfInterest": "FeatureOfInterest",
        "HistoricalLocations": "HistoricalLocation",

        "Thing": "Thing",
        "Location": "Location",
        "Sensor": "Sensor",
        "ObservedProperty": "ObservedProperty",
        "Datastream": "Datastream",
        "Observation": "Observation",  
        "FeatureOfInterest": "FeatureOfInterest",
        "HistoricalLocation": "HistoricalLocation",
    }

    @staticmethod
    def convert_entity(entity: str) -> str:
        """
        Converts an entity name from STA format to REST format.

        Args:
            entity (str): The entity name in STA format.

        Returns:
            str: The converted entity name in REST format.
        """
        return STA2REST.ENTITY_MAPPING.get(entity, entity)
  
    @staticmethod
    def convert_query(full_path: str) -> str:
        """
        Converts a STA query to a PostgREST query.

        Args:
            sta_query (str): The STA query.
        
        Returns:
            str: The converted PostgREST query.
        """

        # check if we have a query
        path = full_path
        query = None
        single_result = False
        if '?' in full_path:
            # Split the query from the path
            path, query = full_path.split('?')

        # Parse the uri
        uri = STA2REST.parse_uri(path)
        
        if not uri:
            raise Exception("Error parsing uri")
        
        main_entity, main_entity_id = uri['entity']
        url = f"/{main_entity}"

        # Check if we have a query
        query_ast = ast.QueryNode(None, None, None, None, None, None, None, False)
        if query:
            lexer = Lexer(query)
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            query_ast = parser.parse()

        entities = uri['entities']
        if entities:
            if not query_ast.expand:
                query_ast.expand = ast.ExpandNode([])
            
            index = 0

            # Merge the entities with the query
            for entity in entities:
                entity_name = entity[0]
                sub_query = ast.QueryNode(None, None, None, None, None, None, None, True)
                if entity[1]:
                    single_result = True
                    sub_query.filter = ast.FilterNode(f"id eq {entity[1]}")

                # Check if we are the last entity
                if index == len(entities) - 1:
                    # Check if we have a property name
                    if uri['property_name']:
                        # Add the property name to the select node
                        if not sub_query.select:
                            sub_query.select = ast.SelectNode([])
                        sub_query.select.identifiers.append(ast.IdentifierNode(uri['property_name']))

                    # Merge the query with the subquery
                    if query_ast.select:
                        sub_query.select = query_ast.select
                        query_ast.select = None

                    if query_ast.filter:
                        sub_query.filter = query_ast.filter
                        query_ast.filter = None

                    if query_ast.orderby:
                        sub_query.orderby = query_ast.orderby
                        query_ast.orderby = None

                    if query_ast.skip:
                        sub_query.skip = query_ast.skip
                        query_ast.skip = None

                    if query_ast.top:
                        sub_query.top = query_ast.top
                        query_ast.top = None

                    if query_ast.count:
                        sub_query.count = query_ast.count
                        query_ast.count = None

                query_ast.expand.identifiers.append(ast.ExpandNodeIdentifier(entity_name, sub_query))
                index += 1
        else:
            if uri['property_name']:
                if not query_ast.select:
                    query_ast.select = ast.SelectNode([])
                query_ast.select.identifiers.append(ast.IdentifierNode(uri['property_name']))

        # Check if we have a filter in the query
        if main_entity_id:
            query_ast.filter = ast.FilterNode(query_ast.filter.filter + f" and id eq {main_entity_id}" if query_ast.filter else f"id eq {main_entity_id}")

            if not entities:
                single_result = True

        # Visit the query ast to convert it
        visitor = NodeVisitor()
        query_converted = visitor.visit(query_ast)

        return {
            'url': url + "?" + query_converted if query_converted else url,
            'ref': uri['ref'],
            'value': uri['value'],
            'single_result': single_result
        }

    @staticmethod
    def parse_entity(entity: str):
        # Check if we have an id in the entity and match only the number
        match = re.search(r'\(\d+\)', entity)
        id = None
        if match:
            # Get the id from the match without the brackets
            id = match.group(0)[1:-1]
            # Remove the id from the entity
            entity = entity.replace(match.group(0), "")

        # Check if the entity is in the ENTITY_MAPPING
        if entity in STA2REST.ENTITY_MAPPING:
            entity = STA2REST.ENTITY_MAPPING[entity]
        else:
            return None

        return (entity, id)
    
    @staticmethod
    def parse_uri(uri: str) -> str:
        # Split the uri by the '/' character
        parts = uri.split('/')
        # Remove the first part
        parts.pop(0)

        # Check if we have a version number
        version = parts.pop(0)

        # Parse first entity
        main_entity = STA2REST.parse_entity(parts.pop(0))
        if not main_entity:
            raise Exception("Error parsing uri: invalid entity")

        # Check all the entities in the uri
        entities = []
        property_name = None
        ref = False
        value = False
        for entity in parts:
            # Parse the entity
            result = STA2REST.parse_entity(entity)
            if result:
                entities.append(result)
            elif entity == "$ref":
                if property_name:
                    raise Exception("Error parsing uri: $ref after property name")
                ref = True
            elif entity == "$value":
                if property_name:
                    value = True
                else:
                    raise Exception("Error parsing uri: $value without property name")
            else:
                property_name = entity

        return {
            'version': version,
            'entity': main_entity,
            'entities': entities,
            'property_name': property_name,
            'ref': ref,
            'value': value
        }


if __name__ == "__main__":
    """
    Example usage of the STA2REST module.

    This example converts a STA query to a REST query.
    """
    query = "/v1.1/Datastreams(1)/Observations(1)/resultTime"
    print("QUERY", query)
    print("CONVERTED", STA2REST.convert_query(query))