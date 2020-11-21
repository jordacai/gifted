function confirmDelete() {
    if (!confirm("Are you sure? There is a chance a gifter already purchased this, and removing it would affect their" +
    " purchase history.")) {
        return false;
    }
}

function confirmUnclaim() {
    if (!confirm("Are you sure? Since you already claimed this item, it may not be picked up by another gifter.")) {
        return false;
    }
}