package me.Sangalaa.Main;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;

import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.Node;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;

public class TZIV_Convertor {
	
	private static final String FILEPATH = "project.jff";
	
	public static void main(String[] args) throws ParserConfigurationException, SAXException, IOException {
		new TZIV_Convertor();
	}
	
	public TZIV_Convertor() throws ParserConfigurationException, SAXException, IOException {
		DocumentBuilderFactory factory = DocumentBuilderFactory.newInstance();
		DocumentBuilder builder = factory.newDocumentBuilder();
		
		Document jFlapFile = builder.parse(new File(FILEPATH));
		jFlapFile.getDocumentElement().normalize();
		
		NodeList nodeList = jFlapFile.getElementsByTagName("state");
		NodeList transitionsList = jFlapFile.getElementsByTagName("transition");
		
		Map<String, String> statesMap = extractStates(nodeList);
		
		String convertedFunction = convertTransitionsToFunction(transitionsList, statesMap);
		
		System.out.println(convertedFunction);
	}
	
	/**
	 * This function is used to construct transition function.
	 * @param transitionsList List of all transitions
	 * @param statesMap Map of indexes mapped to state names
	 * @return Returns transition function in String format
	 */
	public String convertTransitionsToFunction(NodeList transitionsList, Map<String, String> statesMap) {
		if(transitionsList == null || statesMap == null) return null;
		
		Node node = null;
		Element element = null;
		
		String fromAttribute, toAttribute, readAttribute, writeAttribute, moveAttribute;
		
		HashSet<String> workAlphabet = new HashSet<>();
		
		Map<Integer, ArrayList<String>> deltaFunctionsMap = new HashMap<>();
		
		for(int index = 0; index < transitionsList.getLength(); index ++) {
			node = transitionsList.item(index);
			
			if(node.getNodeType() != Node.ELEMENT_NODE) continue;
			
			element = (Element) node;
			
			fromAttribute = element.getElementsByTagName("from").item(0).getTextContent();
			toAttribute = element.getElementsByTagName("to").item(0).getTextContent();
			readAttribute = element.getElementsByTagName("read").item(0).getTextContent();
			writeAttribute = element.getElementsByTagName("write").item(0).getTextContent();
			moveAttribute = element.getElementsByTagName("move").item(0).getTextContent();
			
			if(readAttribute != "") workAlphabet.add(readAttribute);
			if(writeAttribute != "") workAlphabet.add(writeAttribute);
			
			if(readAttribute == "") readAttribute = "blank";
			if(writeAttribute == "") writeAttribute = "blank";
			
			ArrayList<String> deltaList = deltaFunctionsMap.get(Integer.parseInt(fromAttribute));
			if(deltaList == null) {
				deltaList = new ArrayList<>();
				deltaFunctionsMap.put(Integer.parseInt(fromAttribute), deltaList);
			}
			
			deltaList.add(new String("\u03B4(" + statesMap.get(fromAttribute) + "," + readAttribute + ") = (" + statesMap.get(toAttribute) + "," + writeAttribute + "," + moveAttribute + ")\n"));
		}
		
		StringBuilder convertedFunctionBuilder = new StringBuilder();
		
		convertedFunctionBuilder.append("TM = (K,\u03A3,\u0393,\u03B4," + statesMap.get("initial") + ",F)\n");
		convertedFunctionBuilder.append("K = {" + getStatesList(statesMap) + "}\n");
		convertedFunctionBuilder.append("\u03A3 = {TODO}\n");
		convertedFunctionBuilder.append("\u0393 = {");
		
		for(String sign : workAlphabet) convertedFunctionBuilder.append(sign + ",");
		convertedFunctionBuilder.setCharAt(convertedFunctionBuilder.length() - 1, '}');
		
		convertedFunctionBuilder.append("\nF = {" + statesMap.get("finalStates") + "}\n");
		
		List<Integer> sortedKeys = new ArrayList<>(deltaFunctionsMap.keySet());
		Collections.sort(sortedKeys);
		
		for(int key : sortedKeys) {
			List<String> deltaFunctionsArray = deltaFunctionsMap.get(key);
			
			for(String function : deltaFunctionsArray) convertedFunctionBuilder.append(function);
		}
		
		return convertedFunctionBuilder.toString();
	}
	
	/**
	 * This function is used to get list of all states.
	 * @param statesMap Map of indexes mapped to state names
	 * @return Returns list of all states separated by comma
	 */
	public String getStatesList(Map<String, String> statesMap) {
		if(statesMap == null) return null;
		
		StringBuilder statesListBuilder = new StringBuilder();
		
		List<Integer> stateNumbers = new ArrayList<Integer>();
		
		for(String key : statesMap.keySet()) {
			try {
				stateNumbers.add(Integer.parseInt(key));
			}
			catch(NumberFormatException e) {}
		}
		
		Collections.sort(stateNumbers);
		
		for(Integer state : stateNumbers) statesListBuilder.append(statesMap.get(state.toString()) + ",");
		statesListBuilder.deleteCharAt(statesListBuilder.length() - 1);
		
		return statesListBuilder.toString();
	}
	
	/**
	 * This function is used to create map of indexes mapped to state names. It also find initial state and final states.
	 * @param statesList List of states
	 * @return Returns map of indexes mapped to state names
	 */
	public Map<String, String> extractStates(NodeList statesList) {
		if(statesList == null) return null;
		
		Map<String, String> map = new HashMap<>();
		
		Node node = null;
		Element element = null;
		
		List<Integer> finalStatesId = new ArrayList<>();
		
		String attributeId, attributeName;
		
		for(int index = 0; index < statesList.getLength(); index ++) {
			node = statesList.item(index);
			
			if(node.getNodeType() != Node.ELEMENT_NODE) continue;
			
			element = (Element) node;
			
			attributeId = element.getAttribute("id");
			attributeName = element.getAttribute("name");
			
			map.put(attributeId, attributeName);
			
			if(element.getElementsByTagName("initial").item(0) != null) map.put("initial", attributeName);
			if(element.getElementsByTagName("final").item(0) != null) finalStatesId.add(Integer.parseInt(attributeId));
		}
		
		Collections.sort(finalStatesId);
		
		StringBuilder finalStatesBuilder = new StringBuilder();
		
		for(Integer finalState : finalStatesId) finalStatesBuilder.append(map.get(finalState.toString()) + ",");
		
		finalStatesBuilder.deleteCharAt(finalStatesBuilder.length() - 1);
		
		map.put("finalStates", finalStatesBuilder.toString());
		
		return map;
	}

}
