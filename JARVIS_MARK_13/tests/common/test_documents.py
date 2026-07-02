"""
tests/common/test_documents.py

Integration tests for Aether Word & Excel document tools.
Tests creation, reading, modifying, appending, replacing, and range-based querying.
"""

import os
import pytest
from pathlib import Path

from aether.tools.document_tools import (
    create_word, read_word, edit_word,
    create_excel, read_excel, write_excel
)

@pytest.fixture
def temp_dir(tmp_path):
    """Provides a temporary directory path unique to each test."""
    return tmp_path

def test_word_flow(temp_dir):
    """
    Tests Word document flow:
    - Creation with initial content
    - Reading plain text
    - Appending a paragraph
    - Replacing text
    """
    filename = "test_document.docx"
    
    # 1. Create document
    res_create = create_word(
        filename=filename,
        directory=str(temp_dir),
        content="Monthly Report Summary",
        overwrite=True
    )
    assert res_create["success"] is True
    path = res_create["data"]["path"]
    assert Path(path).exists()
    
    # 2. Read document
    res_read = read_word(file_path=path)
    assert res_read["success"] is True
    assert "Monthly Report Summary" in res_read["data"]["content"]
    
    # 3. Append text
    res_append = edit_word(
        file_path=path,
        operation="append",
        text="Appended text paragraph at the end."
    )
    assert res_append["success"] is True
    
    res_read2 = read_word(file_path=path)
    assert "Appended text paragraph at the end." in res_read2["data"]["content"]
    
    # 4. Replace text
    res_replace = edit_word(
        file_path=path,
        operation="replace",
        old_text="Monthly",
        new_text="Weekly"
    )
    assert res_replace["success"] is True
    
    res_read3 = read_word(file_path=path)
    assert "Weekly Report Summary" in res_read3["data"]["content"]
    assert "Monthly Report Summary" not in res_read3["data"]["content"]

def test_excel_flow(temp_dir):
    """
    Tests Excel workbook flow:
    - Workbook creation
    - Writing to individual cells
    - Range reading
    - Entire worksheet reading
    """
    filename = "test_ledger.xlsx"
    sheet_name = "LedgerSheet"
    
    # 1. Create Excel Workbook
    res_create = create_excel(
        filename=filename,
        directory=str(temp_dir),
        sheet_name=sheet_name,
        overwrite=True
    )
    assert res_create["success"] is True
    path = res_create["data"]["path"]
    assert Path(path).exists()
    
    # 2. Write cells
    res_write1 = write_excel(file_path=path, sheet_name=sheet_name, cell="A1", value="Title")
    assert res_write1["success"] is True
    
    res_write2 = write_excel(file_path=path, sheet_name=sheet_name, cell="A2", value="Income")
    assert res_write2["success"] is True
    
    res_write3 = write_excel(file_path=path, sheet_name=sheet_name, cell="B1", value="Amount")
    assert res_write3["success"] is True
    
    res_write4 = write_excel(file_path=path, sheet_name=sheet_name, cell="B2", value=4500)
    assert res_write4["success"] is True
    
    # 3. Read specific range (A1:B2 grid)
    res_read_range = read_excel(file_path=path, sheet_name=sheet_name, cell_range="A1:B2")
    assert res_read_range["success"] is True
    cells = res_read_range["data"]["cells"]
    assert cells == [["Title", "Amount"], ["Income", 4500]]
    
    # 4. Read entire worksheet
    res_read_all = read_excel(file_path=path, sheet_name=sheet_name)
    assert res_read_all["success"] is True
    cells_all = res_read_all["data"]["cells"]
    assert cells_all[0][0] == "Title"
    assert cells_all[1][0] == "Income"

def test_category_expansion():
    """
    Validates that the CategoryEngine correctly matches natural language keywords
    (like 'word', 'docx', 'excel', 'xlsx', 'cell', 'sheet') to document tools.
    """
    from aether.llm.category_engine import CategoryEngine
    
    # 1. Test word queries
    candidates_word = CategoryEngine.get_candidate_tools("Create a meeting notes Word document", [])
    assert "create_word" in candidates_word
    assert "read_word" in candidates_word
    assert "edit_word" in candidates_word
    
    # 2. Test excel queries
    candidates_excel = CategoryEngine.get_candidate_tools("Write 500 into cell A1 of the budget sheet", [])
    assert "create_excel" in candidates_excel
    assert "read_excel" in candidates_excel
    assert "write_excel" in candidates_excel

def test_rule_validator_repairs():
    """
    Validates that the rule validator correctly auto-repairs missing 'filename'
    parameters in 'create_word' and 'create_excel' steps when 'content' or
    'sheet_name' represents the intended file name.
    """
    from aether.validation.rule_validator import validate_plan_steps
    
    # 1. Test create_word auto-repair
    steps_word = [
        {
            "tool": "create_word",
            "arguments": {
                "content": "Report"
            }
        }
    ]
    is_valid, errors = validate_plan_steps(steps_word)
    assert is_valid is True
    assert len(errors) == 0
    assert steps_word[0]["arguments"]["filename"] == "Report"
    
    # 2. Test create_excel auto-repair
    steps_excel = [
        {
            "tool": "create_excel",
            "arguments": {
                "sheet_name": "Sales.xlsx"
            }
        }
    ]
    is_valid, errors = validate_plan_steps(steps_excel)
    assert is_valid is True
    assert len(errors) == 0
    assert steps_excel[0]["arguments"]["filename"] == "Sales.xlsx"


