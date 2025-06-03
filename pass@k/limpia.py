input = """
#include <iostream>
#include <vector>
#include <cassert>

// Estructura base (debes adaptar si la definición original cambia)
struct ListNode {
    int val;
    ListNode* next;
    ListNode(int x) : val(x), next(nullptr) {}
};

// 🧠 Declaración de la función implementada en el archivo modificado
ListNode* reverseList(ListNode* head);

// 🔍 Función auxiliar para crear una lista desde un vector
ListNode* createList(const std::vector<int>& values) {
    ListNode dummy(0);
    ListNode* current = &dummy;
    for (int val : values) {
        current->next = new ListNode(val);
        current = current->next;
    }
    return dummy.next;
}

// 🧪 Función auxiliar para convertir lista a vector
std::vector<int> listToVector(ListNode* head) {
    std::vector<int> result;
    while (head) {
        result.push_back(head->val);
        head = head->next;
    }
    return result;
}

// ✅ Test unitario
void runTest() {
    ListNode* input = createList({1, 2, 3, 4, 5});
    ListNode* reversed = reverseList(input);
    std::vector<int> result = listToVector(reversed);
    std::vector<int> expected = {5, 4, 3, 2, 1};
    assert(result == expected);
    std::cout << "✅ Test passed!" << std::endl;
}

int main() {
    runTest();
    return 0;
}
"""

inputLimpia = input.replace("\n", "")
print(inputLimpia) # Imprimirá: Hola, mundo!