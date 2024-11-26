from action_generator import generate_random_action_sequence, save_actions_to_csv

# Generate a random action sequence
sequence = generate_random_action_sequence()

# Save the generated sequence to a CSV file
save_actions_to_csv(sequence)

print("Test completed: Random action sequence generated and saved to CSV.")
