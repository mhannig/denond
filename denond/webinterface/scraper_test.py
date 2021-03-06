

import pytest
import scraper

from denond.tests.utils import read_sample_data

def test_parse_assigned_inputs():
    """Test assigned inputs extraction"""
    html = read_sample_data("assigned_inputs.html")
    mapping = scraper.parse_assigned_inputs(html)

    expected = [('listHdmiAssignBD', 'OFF'),
                ('listHdmiAssignSAT/CBL', 'HD3')]

    for (k, v) in expected:
        assert mapping[k] == v

    # There should be 5 * 8 keys
    assert len(mapping) == 40
