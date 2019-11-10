function confirmDelete() {
    if (!confirm("Are you sure? Since you already claimed this item, it may not be picked up by another gifter.")) {
        return false;
    }
}