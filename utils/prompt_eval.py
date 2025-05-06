import numpy as np
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import defaultdict

def prompt_evaluation(llm, chains, data_fetcher, year, month, user_ids_by_segment):
    """
    Evaluate different prompting approaches for generating financial reports for multiple users,
    measuring success rate, response time, cost, and similarity within and across segments.
    
    Args:
        llm: The language model to use
        chains: Dictionary of LLMChains for different prompting approaches
        data_fetcher: DataFetcher instance to get user transaction data
        year: Year for the reports
        month: Month for the reports
        user_ids_by_segment: Dictionary mapping segment names to lists of user IDs
    
    Returns:
        tuple: (detailed_results, segment_results, cross_segment_similarity)
    """
    # Define financial report components and prompting approaches
    components = {
        "executive_summary": ["zero_shot", "few_shot", "chain_of_thought"],
        "cash_flow": ["chain_of_thought"],
        "transaction_behaviour": ["chain_of_thought"]
    }
    
    # Initialize result structures
    detailed_results = {}  # Results for each user
    segment_results = {}   # Aggregated results by segment
    outputs_by_segment = {}  # Store outputs for similarity analysis
    
    # Cost by Claude 3.7 Sonnet model
    cost_per_input_token = 0.000015
    cost_per_output_token = 0.000075
    chars_per_token = 4  # Assuming ~4 characters per token
    
    # Initialize segment results structure
    for segment in user_ids_by_segment:
        segment_results[segment] = {}
        outputs_by_segment[segment] = {}
        
        for component in components:
            segment_results[segment][component] = {}
            outputs_by_segment[segment][component] = {}
            
            for approach in components[component]:
                segment_results[segment][component][approach] = {
                    "success_rate": 0,
                    "total_users": 0,
                    "avg_response_time": 0,
                    "avg_cost": 0,
                    "within_segment_similarity": 0,
                    "outputs": []
                }
                outputs_by_segment[segment][component][approach] = []
    
    # Process each segment and user
    for segment, user_ids in user_ids_by_segment.items():
        for user_id in user_ids:
            print(f"Processing user {user_id} in segment {segment}...")
            
            # Get user's transaction summary
            try:
                transaction_summary = data_fetcher.monthly_profile(year=year, month=month, user_id=user_id)
                
                # Initialize results for this user
                user_key = f"{segment}_{user_id}"
                detailed_results[user_key] = {}
                
                # Process each component for this user
                for component in components:
                    detailed_results[user_key][component] = {}
                    
                    for approach in components[component]:
                        # Use the approach directly as the chain key
                        chain_key = approach
                        
                        # Prepare inputs
                        inputs = {"transaction_summary": transaction_summary}
                        
                        # Get the prompt template
                        prompt_template = chains[chain_key].steps[0].template
                        input_text = prompt_template.format(**inputs)
                        input_tokens = len(input_text) / chars_per_token
                        
                        # Run the chain
                        start_time = time.time()
                        try:
                            output = chains[chain_key].invoke(inputs)
                            success = True
                            # Extract just the content from the output dictionary
                            output_content = output.get(approach, output)
                            if isinstance(output_content, dict):
                                output_text = str(output_content)
                            else:
                                output_text = str(output_content)
                        except Exception as e:
                            print(f"Error generating {component} for user {user_id} with {approach}: {e}")
                            success = False
                            output_text = ""
                            
                        response_time = time.time() - start_time
                        
                        # Calculate output tokens for cost estimation
                        output_tokens = len(output_text) / chars_per_token
                        
                        # Calculate cost
                        estimated_cost = (input_tokens * cost_per_input_token) + (output_tokens * cost_per_output_token)
                        
                        # Record metrics for this user
                        detailed_results[user_key][component][approach] = {
                            "success": success,
                            "response_time": response_time,
                            "cost": estimated_cost,
                            "output": output_text
                        }
                        
                        # Update segment aggregates
                        segment_results[segment][component][approach]["total_users"] += 1
                        if success:
                            segment_results[segment][component][approach]["success_rate"] += 1
                            segment_results[segment][component][approach]["avg_response_time"] += response_time
                            segment_results[segment][component][approach]["avg_cost"] += estimated_cost
                            
                            # Store output for similarity analysis
                            if output_text:
                                outputs_by_segment[segment][component][approach].append(output_text)
                                segment_results[segment][component][approach]["outputs"].append(output_text)
            
            except Exception as e:
                print(f"Error processing user {user_id}: {e}")
                continue
    
    # Calculate averages and within-segment similarity
    vectorizer = TfidfVectorizer()
    
    for segment in segment_results:
        for component in components:
            for approach in components[component]:
                # Calculate averages
                successful_users = segment_results[segment][component][approach]["success_rate"]
                total_users = segment_results[segment][component][approach]["total_users"]
                
                if successful_users > 0:
                    segment_results[segment][component][approach]["success_rate"] = successful_users / total_users
                    segment_results[segment][component][approach]["avg_response_time"] /= successful_users
                    segment_results[segment][component][approach]["avg_cost"] /= successful_users
                    
                    # Calculate within-segment similarity
                    outputs = outputs_by_segment[segment][component][approach]
                    if len(outputs) > 1:
                        try:
                            tfidf_matrix = vectorizer.fit_transform(outputs)
                            similarity_matrix = cosine_similarity(tfidf_matrix)
                            # Average similarity excluding self-comparisons (diagonal)
                            avg_similarity = (np.sum(similarity_matrix) - len(outputs)) / (len(outputs) * (len(outputs) - 1))
                            segment_results[segment][component][approach]["within_segment_similarity"] = avg_similarity
                        except Exception as e:
                            print(f"Error calculating similarity for {segment} {component} {approach}: {e}")
                            segment_results[segment][component][approach]["within_segment_similarity"] = 0
                else:
                    segment_results[segment][component][approach]["success_rate"] = 0
                    segment_results[segment][component][approach]["avg_response_time"] = 0
                    segment_results[segment][component][approach]["avg_cost"] = 0
                    segment_results[segment][component][approach]["within_segment_similarity"] = 0
    
    # Calculate cross-segment similarity
    cross_segment_similarity = {}
    
    for component in components:
        cross_segment_similarity[component] = {}
        
        for approach in components[component]:
            cross_segment_similarity[component][approach] = {}
            
            # Get all segments with at least one successful output
            segments_with_outputs = [
                segment for segment in segment_results
                if len(outputs_by_segment[segment][component][approach]) > 0
            ]
            
            # Skip if fewer than 2 segments have outputs
            if len(segments_with_outputs) < 2:
                continue
            
            # Compare each pair of segments
            for i, segment1 in enumerate(segments_with_outputs):
                cross_segment_similarity[component][approach][segment1] = {}
                
                for segment2 in segments_with_outputs[i+1:]:
                    outputs1 = outputs_by_segment[segment1][component][approach]
                    outputs2 = outputs_by_segment[segment2][component][approach]
                    
                    # Skip if either segment has no outputs
                    if not outputs1 or not outputs2:
                        continue
                    
                    try:
                        # Combine outputs from both segments
                        all_outputs = outputs1 + outputs2
                        # Create segment labels for each output
                        segment_labels = [segment1] * len(outputs1) + [segment2] * len(outputs2)
                        
                        # Calculate TF-IDF matrix
                        tfidf_matrix = vectorizer.fit_transform(all_outputs)
                        similarity_matrix = cosine_similarity(tfidf_matrix)
                        
                        # Calculate average similarity between segments
                        cross_similarity_sum = 0
                        cross_similarity_count = 0
                        
                        for i in range(len(all_outputs)):
                            for j in range(i+1, len(all_outputs)):
                                # Only include pairs where outputs are from different segments
                                if segment_labels[i] != segment_labels[j]:
                                    cross_similarity_sum += similarity_matrix[i, j]
                                    cross_similarity_count += 1
                        
                        if cross_similarity_count > 0:
                            avg_cross_similarity = cross_similarity_sum / cross_similarity_count
                            cross_segment_similarity[component][approach][segment1][segment2] = avg_cross_similarity
                    except Exception as e:
                        print(f"Error calculating cross-segment similarity between {segment1} and {segment2}: {e}")
                        cross_segment_similarity[component][approach][segment1][segment2] = 0
    
    # Determine best approach for each segment and component
    best_approaches = {}
    
    for segment in segment_results:
        best_approaches[segment] = {}
        
        for component, approaches in components.items():
            # Filter to valid approaches (with successful outputs)
            valid_approaches = [
                a for a in approaches 
                if segment_results[segment][component][a]["success_rate"] > 0
            ]
            
            if not valid_approaches:
                best_approaches[segment][component] = None
                continue
                
            if len(valid_approaches) == 1:
                best_approaches[segment][component] = valid_approaches[0]
                continue
            
            # Find max values for normalization
            max_response_time = max(segment_results[segment][component][a]["avg_response_time"] for a in valid_approaches)
            max_cost = max(segment_results[segment][component][a]["avg_cost"] for a in valid_approaches)
            
            if max_response_time == 0:
                max_response_time = 1
            if max_cost == 0:
                max_cost = 1
                
            # Select best approach based on weighted metrics
            best_approaches[segment][component] = max(
                valid_approaches,
                key=lambda a: (
                    segment_results[segment][component][a]["success_rate"] * 0.4 +
                    (1 - segment_results[segment][component][a]["avg_response_time"] / max_response_time) * 0.15 +
                    (1 - segment_results[segment][component][a]["within_segment_similarity"]) * 0.35 +  # Lower similarity is better for personalization
                    (1 - segment_results[segment][component][a]["avg_cost"] / max_cost) * 0.1
                )
            )
    
    return detailed_results, segment_results, cross_segment_similarity, best_approaches

def generate_evaluation_report(segment_results, cross_segment_similarity, best_approaches):
    """
    Generate a summary report of the evaluation results
    
    Args:
        segment_results: Dictionary of segment-level results
        cross_segment_similarity: Dictionary of cross-segment similarity scores
        best_approaches: Dictionary of best approaches for each segment and component
        
    Returns:
        str: Text report summarizing the results
    """
    report_lines = ["# Prompt Evaluation Report\n"]
    
    # Best approaches summary
    report_lines.append("## Best Prompting Approaches by Segment\n")
    for segment, components in best_approaches.items():
        report_lines.append(f"### {segment}\n")
        for component, approach in components.items():
            if approach:
                report_lines.append(f"- {component}: **{approach}**\n")
                metrics = segment_results[segment][component][approach]
                report_lines.append(f"  - Success Rate: {metrics['success_rate']:.2%}\n")
                report_lines.append(f"  - Avg Response Time: {metrics['avg_response_time']:.2f}s\n")
                report_lines.append(f"  - Avg Cost: ${metrics['avg_cost']:.4f}\n")
                report_lines.append(f"  - Within-Segment Similarity: {metrics['within_segment_similarity']:.4f}\n")
            else:
                report_lines.append(f"- {component}: No successful approach\n")
        report_lines.append("\n")
    
    # Segment performance summary
    report_lines.append("## Segment Performance Summary\n")
    for segment, components in segment_results.items():
        report_lines.append(f"### {segment}\n")
        for component, approaches in components.items():
            report_lines.append(f"#### {component}\n")
            report_lines.append("| Approach | Success Rate | Avg Response Time | Avg Cost | Within-Segment Similarity |\n")
            report_lines.append("|----------|-------------|-------------------|----------|-------------------------|\n")
            
            for approach, metrics in approaches.items():
                report_lines.append(
                    f"| {approach} | {metrics['success_rate']:.2%} | {metrics['avg_response_time']:.2f}s | "
                    f"${metrics['avg_cost']:.4f} | {metrics['within_segment_similarity']:.4f} |\n"
                )
            report_lines.append("\n")
    
    # Cross-segment similarity summary
    report_lines.append("## Cross-Segment Similarity\n")
    for component, approaches in cross_segment_similarity.items():
        report_lines.append(f"### {component}\n")
        
        for approach, segments in approaches.items():
            report_lines.append(f"#### {approach}\n")
            
            if not segments:
                report_lines.append("No cross-segment data available\n\n")
                continue
                
            report_lines.append("| Segment Pair | Similarity |\n")
            report_lines.append("|-------------|------------|\n")
            
            for segment1, segment2_scores in segments.items():
                for segment2, score in segment2_scores.items():
                    report_lines.append(f"| {segment1} - {segment2} | {score:.4f} |\n")
            
            report_lines.append("\n")
    
    return "".join(report_lines)

def run_evaluation(llm, chains, data_fetcher, year, month, user_selection="all"):
    """
    Run the enhanced prompt evaluation with configurable user selection
    
    Args:
        llm: The language model to use
        chains: Dictionary of LLMChains for different prompting approaches
        data_fetcher: DataFetcher instance to get user transaction data
        year: Year for the reports
        month: Month for the reports
        user_selection: "all" to use all users, or a number to use a subset of users per segment
    
    Returns:
        tuple: (detailed_results, segment_results, cross_segment_similarity, best_approaches, report)
    """
    # Get user segments
    segment_users = data_fetcher.get_segment_users(
        year=year,
        month=month,
        min_transactions=3,
        max_users=50 if user_selection == "all" else int(user_selection)
    )
    
    # Run evaluation
    detailed_results, segment_results, cross_segment_similarity, best_approaches = prompt_evaluation(
        llm, chains, data_fetcher, year, month, segment_users
    )
    
    # Generate report
    report = generate_evaluation_report(segment_results, cross_segment_similarity, best_approaches)
    
    return detailed_results, segment_results, cross_segment_similarity, best_approaches, report