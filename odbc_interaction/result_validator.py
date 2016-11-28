import re

from jmx_interaction.structures import RequestStructure, QueryType, AssertionField, ValidationType
from utils.util import IncorrectValidationException


def validate_result(request, actual_result):
    """
    @type request: jmx_interaction.structures.RequestStructure
    @type actual_result: dict
    """
    query_type = request.query_type
    assertion_field = None
    validation_type = None
    """:type: ValidationType"""
    ignore_status = None
    for expected_result in request.expected_results:
        assertion_field = expected_result.assertion_field
        validation_type = expected_result.validation_type
        ignore_status = expected_result.ignore_status
        break
    actual_exception = actual_result.get("exception")
    if actual_exception is not None and not ignore_status:
        return {False: str(actual_exception)}

    for expected_result in request.expected_results:
        if query_type == QueryType.Update:
            if assertion_field == AssertionField.ResponseMessage:
                # todo: add validation here when response message in will be presented in exception error message
                return {True: ""}
            if assertion_field == AssertionField.ResponseData:
                expected = expected_result.request_result
                expected_row_count = get_number_from_message(expected)
                actual = actual_result.get("row_count")
                if expected_row_count != actual:
                    return {
                        False: "expected row count [" + expected + "] was not found in actual result [" + actual + "] full expected result: [" + expected + "]"}
            else:
                return {True: ""}
        if request.query_type == QueryType.Select:
            if assertion_field == AssertionField.ResponseMessage:
                expected = expected_result.request_result
                actual = ""
                if actual_exception is not None:
                    actual = str(actual_exception)
                return validate_using_validation_type(expected, actual, validation_type)


"""
exceptions can be only for SELECT "table doesn't exists" for example
responses also can have variables

"update queries" can be validated using row_count
to validate UPDATE:
    if ResponseMessage - only check that row_count == 0
    if ResponseText - extract number of expected updates from expected result, compare it with row_count

to validate SELECT:
    if ResponseMessage - expected result should be smartly compared with "exception".message
    if ResponseText - expected result should be converted to list of dicts and compared to result of request
        names of columns should be ignored
"""


def validate_using_validation_type(expected, actual, validation_type):
    """
        @type expected: str
        @type actual: str
        @type validation_type: ValidationType
    """
    if validation_type == ValidationType.Equals:
        if expected.lower() != actual.lower():
            return {False: "expected != actual: [" + expected + "] != [" + actual + "]"}
        return {True: ""}
    if validation_type == ValidationType.Substring:
        if expected.lower() not in actual.lower():
            return {False: "actual string [" + actual + "] doesn't have expected [" + expected + "] substring"}
        return {True: ""}
    if validation_type == ValidationType.Contains:
        regex = re.compile(expected)
        if regex.search(actual) is None:
            return {False: "actual string [" + actual + "] doesn't contains expected [" + expected + "]"}
        return {True: ""}
    if validation_type == ValidationType.Matches:
        m = re.match(actual, expected)
        if not m:
            return {False: "actual string [" + actual + "] doesn't match expected pattern [" + expected + "]"}
        return {True: ""}


def get_number_from_message(message):
    """
    @type message: str
    """
    m = re.match("^(\d+)", message)
    if m:
        return m.group(1)
