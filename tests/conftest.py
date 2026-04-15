"""
Pytest configuration and fixtures for DS API Review Tool tests.
"""

import pytest
from pathlib import Path


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_routes_content() -> str:
    """Sample Laravel routes file content for testing."""
    return """<?php

use App\\Http\\Controllers\\Api\\External\\UnitsController;
use App\\Http\\Controllers\\Api\\External\\ReservationsController;
use Illuminate\\Support\\Facades\\Route;

Route::prefix('v1')->middleware(['auth:api'])->group(function () {
    Route::get('/units', [UnitsController::class, 'index'])->middleware(['scope:units:read']);
    Route::post('/units', [UnitsController::class, 'store'])->middleware(['scope:units:write']);
    Route::get('/reservations', [ReservationsController::class, 'index'])->middleware(['scope:reservations:read']);
});
"""
